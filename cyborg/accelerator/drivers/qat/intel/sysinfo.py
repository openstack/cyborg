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
Cyborg Intel QAT driver implementation.
"""


import glob
import os
import socket

from cyborg.accelerator.common import utils
from cyborg.common import constants
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_attribute
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device

from oslo_serialization import jsonutils


PCI_DEVICES_PATH = "/sys/bus/pci/devices"
KNOW_QATS = [("0x8086", "0x37c8")]
PF = "physfn"
VF = "virtfn*"
INTEL_QAT_DEV_PREFIX = "intel-qat-dev"
RC_QAT = constants.RESOURCES["QAT"]
DRIVER_NAME = "intel"

RESOURCES = {
    "qat": RC_QAT
}


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


def get_link_targets(links):
    return map(
        lambda p:
            os.path.realpath(
                os.path.join(os.path.dirname(p), os.readlink(p))),
        links)


def all_qats():
    return set(filter(
        lambda p: (
            pci_attributes(p)["VENDOR"],
            pci_attributes(p)["PRODUCT_ID"]
        ) in KNOW_QATS,
        glob.glob(os.path.join(PCI_DEVICES_PATH, "*"))))


def all_pfs_with_vf():
    return set(filter(
        lambda p: glob.glob(os.path.join(p, VF)),
        all_qats()))


def all_vfs_in_pf(pf_path):
    return map(
        lambda p:
        os.path.join(
            os.path.dirname(os.path.dirname(p)),
            os.path.basename(os.readlink(p))),
        glob.glob(os.path.join(pf_path, VF)))


def find_pf_by_vf(vf_path):
    return os.path.join(
        os.path.dirname(vf_path),
        os.path.basename(os.readlink(
            os.path.join(vf_path, PF))))


def all_vfs():
    return map(
        lambda p: all_vfs_in_pf(p), all_pfs_with_vf()
    )


def qat_gen(path):
    pci_info = pci_attributes(path)
    qat = {
        "name": "_".join((socket.gethostname(), pci_info["PCI_SLOT_NAME"])),
        "device": pci_info["PCI_SLOT_NAME"],
        "type": constants.DEVICE_QAT,
        "vendor": pci_info["VENDOR"],
        "product_id": pci_info["PRODUCT_ID"],
        "rc": RESOURCES["qat"],
        "stub": False,
    }
    return qat


def qat_tree():
    devs = []
    pfs_has_vf = all_pfs_with_vf()
    for q in all_qats():
        qat = qat_gen(q)
        if q in pfs_has_vf:
            vfs = []
            for vf in all_vfs_in_pf(q):
                vf_qat = qat_gen(vf)
                vfs.append(vf_qat)
            qat["vfs"] = vfs
        devs.append(_generate_driver_device(qat))
    return devs


def _generate_driver_device(qat):
    driver_device_obj = driver_device.DriverDevice()
    driver_device_obj.vendor = qat["vendor"]
    driver_device_obj.stub = qat["stub"]
    driver_device_obj.model = qat.get("model", "miss_model_info")
    driver_device_obj.vendor_board_info = qat.get(
        "vendor_board_info",
        "miss_vb_info")
    std_board_info = {"product_id": qat.get("product_id", None)}
    driver_device_obj.std_board_info = jsonutils.dumps(std_board_info)
    driver_device_obj.type = qat["type"]
    driver_device_obj.controlpath_id = _generate_controlpath_id(qat)
    driver_device_obj.deployable_list = _generate_dep_list(qat)
    return driver_device_obj


def _generate_controlpath_id(qat):
    driver_cpid = driver_controlpath_id.DriverControlPathID()
    driver_cpid.cpid_type = "PCI"
    driver_cpid.cpid_info = utils.pci_str_to_json(qat["device"])
    return driver_cpid


def _generate_dep_list(qat):
    dep_list = []
    # pf without sriov enabled.
    if "vfs" not in qat:
        driver_dep = driver_deployable.DriverDeployable()
        driver_dep.num_accelerators = 1
        driver_dep.attach_handle_list = [
            _generate_attach_handle(qat)]
        driver_dep.name = qat["name"]
        driver_dep.driver_name = DRIVER_NAME
        driver_dep.attribute_list = _generate_attribute_list(qat)
        dep_list = [driver_dep]
    # pf with sriov enabled, may have several vfs.
    else:
        for vf in qat["vfs"]:
            driver_dep = driver_deployable.DriverDeployable()
            driver_dep.num_accelerators = 1
            driver_dep.attach_handle_list = [
                _generate_attach_handle(vf)]
            driver_dep.name = vf["name"]
            driver_dep.driver_name = DRIVER_NAME
            driver_dep.attribute_list = _generate_attribute_list(qat)
            dep_list.append(driver_dep)
    return dep_list


def _generate_attach_handle(qat):
    driver_ah = driver_attach_handle.DriverAttachHandle()
    driver_ah.attach_type = "PCI"
    driver_ah.attach_info = utils.pci_str_to_json(qat["device"])
    driver_ah.in_use = False
    return driver_ah


def _generate_attribute_list(qat):
    attr_list = []
    for k, _ in qat.items():
        if k == "rc":
            driver_attr = driver_attribute.DriverAttribute()
            driver_attr.key = k
            driver_attr.value = qat.get(k, None)
            attr_list.append(driver_attr)
    return attr_list
