# Copyright 2020 Intel, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


"""
Cyborg Intel NIC driver implementation.
"""


import glob
import os
import socket

from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils

from cyborg.accelerator.common import utils
import cyborg.conf

from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_attribute
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device

LOG = logging.getLogger(__name__)

PCI_DEVICES_PATH_PATTERN = "/sys/bus/pci/devices/*"
KNOWN_NICS = [("0x8086", "0x158b"), ("0x8086", "0x1572")]
DRIVER_NAME = "intel"

VF = "virtfn*"
_SRIOV_TOTALVFS = "sriov_totalvfs"
CONF = cyborg.conf.CONF


def _parse_config():
    # parse nic config.
    cyborg.conf.devices.register_dynamic_opts(CONF)
    try:
        pdm = utils.parse_mappings(CONF.x710_static.physical_device_mappings)
        fdm = utils.parse_mappings(CONF.x710_static.function_device_mappings)
    except cfg.NoSuchOptError:
        return None, None
    else:
        return pdm, fdm


def get_physical_network_and_traits(pci_info, physnet_device_mappings,
                                    function_device_mappings, pf_nic=None):
    traits = []
    physnet = None
    func_name = None

    if pf_nic:
        pf_addr = pf_nic["device"]
        traits.append("CUSTOM_VF")
    else:
        pf_addr = pci_info["PCI_SLOT_NAME"]
        traits.append("CUSTOM_PF")
    if not pf_addr:
        LOG.error("Incorrect report data received. Missing PF info.")

    pf_ifname = utils.get_ifname_by_pci_address(pf_addr)

    if physnet_device_mappings:
        for key, devices in physnet_device_mappings.items():
            if pf_ifname in devices:
                physnet = key
                break
    if function_device_mappings:
        for key, devices in function_device_mappings.items():
            if pf_ifname in devices:
                func_name = key
                break
    if func_name:
        traits.append("CUSTOM_" + func_name.upper())
    if physnet:
        traits.append("CUSTOM_" + physnet.upper())

    return {"traits": traits, "physical_network": physnet}


def read_line(filename):
    with open(filename) as f:
        return f.readline().strip()


def find_nics_by_know_list():
    return set(filter(
        lambda p: (
            read_line(os.path.join(p, "vendor")),
            read_line(os.path.join(p, "device"))
        ) in KNOWN_NICS,
        glob.glob(PCI_DEVICES_PATH_PATTERN)))


def pci_attributes(path):
    with open(os.path.join(path, "uevent")) as f:
        attributes = dict(map(
            lambda p: p.strip().split("="),
            f.readlines()
        ))

    with open(os.path.join(path, "vendor")) as f:
        attributes["VENDOR"] = f.readline().strip()

    with open(os.path.join(path, "device")) as f:
        attributes["PRODUCT_ID"] = f.readline().strip()

    return attributes


def nic_gen(path, physnet_device_mappings=None, function_device_mappings=None,
            pf_nic=None):
    pci_info = pci_attributes(path)
    nic = {
        "name": "_".join((socket.gethostname(), pci_info["PCI_SLOT_NAME"])),
        "device": pci_info["PCI_SLOT_NAME"],
        "type": "NIC",
        "vendor": pci_info["VENDOR"],
        "product_id": pci_info["PRODUCT_ID"],
        "rc": "CUSTOM_NIC",
        "stub": False,
        }
    # TODO(Xinran): need check device id and call get_traits differently.
    updates = get_physical_network_and_traits(pci_info,
                                              physnet_device_mappings,
                                              function_device_mappings,
                                              pf_nic)

    nic.update(updates)
    return nic


def all_pfs_with_vf():
    return set(filter(
        lambda p: glob.glob(os.path.join(p, VF)),
        find_nics_by_know_list()))


def all_vfs_in_pf(pf_path):
    return map(
        lambda p:
        os.path.join(
            os.path.dirname(os.path.dirname(p)),
            os.path.basename(os.readlink(p))),
        glob.glob(os.path.join(pf_path, VF)))


def nic_tree():
    physnet_device_mappings, function_device_mappings = _parse_config()
    nics = []
    pfs_has_vf = all_pfs_with_vf()
    for n in find_nics_by_know_list():
        nic = nic_gen(n, physnet_device_mappings, function_device_mappings)
        if n in pfs_has_vf:
            vfs = []
            for vf in all_vfs_in_pf(n):
                vf_nic = nic_gen(vf, physnet_device_mappings,
                                 function_device_mappings, nic)
                vfs.append(vf_nic)
            nic["vfs"] = vfs
        nics.append(_generate_driver_device(nic))
    return nics


def _generate_driver_device(nic):
    driver_device_obj = driver_device.DriverDevice()
    driver_device_obj.vendor = nic["vendor"]
    driver_device_obj.stub = nic["stub"]
    driver_device_obj.model = nic.get("model", "miss_model_info")
    driver_device_obj.vendor_board_info = nic.get(
        "vendor_board_info",
        "miss_vb_info")
    std_board_info = {"product_id": nic.get("product_id")}
    driver_device_obj.std_board_info = jsonutils.dumps(std_board_info)
    driver_device_obj.type = nic["type"]
    driver_device_obj.controlpath_id = _generate_controlpath_id(nic)
    driver_device_obj.deployable_list = _generate_dep_list(nic)
    return driver_device_obj


def _generate_controlpath_id(nic):
    driver_cpid = driver_controlpath_id.DriverControlPathID()
    driver_cpid.cpid_type = "PCI"
    driver_cpid.cpid_info = utils.pci_str_to_json(nic["device"])
    return driver_cpid


def _generate_dep_list(nic):
    dep_list = []
    # pf without sriov enabled.
    if "vfs" not in nic:
        driver_dep = driver_deployable.DriverDeployable()
        driver_dep.num_accelerators = 1
        driver_dep.attach_handle_list = [
            _generate_attach_handle(nic)]
        driver_dep.name = nic["name"]
        driver_dep.driver_name = DRIVER_NAME
        driver_dep.attribute_list = _generate_attribute_list(nic)
        dep_list = [driver_dep]
    # pf with sriov enabled, may have several vfs.
    else:
        for vf in nic["vfs"]:
            driver_dep = driver_deployable.DriverDeployable()
            driver_dep.num_accelerators = 1
            driver_dep.attach_handle_list = [
                _generate_attach_handle(vf)]
            driver_dep.name = vf["name"]
            driver_dep.driver_name = DRIVER_NAME
            driver_dep.attribute_list = _generate_attribute_list(vf)
            dep_list.append(driver_dep)
    return dep_list


def _generate_attach_handle(nic):
    driver_ah = driver_attach_handle.DriverAttachHandle()
    driver_ah.attach_type = "PCI"
    driver_ah.attach_info = utils.pci_str_to_json(nic["device"],
                                                  nic["physical_network"])
    driver_ah.in_use = False
    return driver_ah


def _generate_attribute_list(nic):
    attr_list = []
    for k, v in nic.items():
        if k == "rc":
            driver_attr = driver_attribute.DriverAttribute()
            driver_attr.key, driver_attr.value = k, v
            attr_list.append(driver_attr)
        if k == "traits":
            values = nic.get(k, [])
            for index, val in enumerate(values):
                driver_attr = driver_attribute.DriverAttribute()
                driver_attr.key = "trait" + str(index)
                driver_attr.value = val
                attr_list.append(driver_attr)

    return attr_list
