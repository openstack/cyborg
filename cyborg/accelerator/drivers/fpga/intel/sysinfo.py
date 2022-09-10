# Copyright 2018 Intel, Inc.
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
Cyborg Intel FPGA driver implementation.
"""


import glob
import os
import re
import socket

from oslo_serialization import jsonutils

from cyborg.accelerator.common import utils
from cyborg.common import constants
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_attribute
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device


PCI_DEVICES_PATH = "/sys/bus/pci/devices"
PCI_DEVICES_PATH_PATTERN = "/sys/bus/pci/devices/*"
# TODO(shaohe) The KNOWN_FPGAS can be configurable.
KNOWN_FPGAS = [("0x8086", "0x09c4")]

SYS_FPGA = "/sys/class/fpga"
DEVICE = "device"
PF = "physfn"
VF = "virtfn*"
BDF_PATTERN = re.compile(
    r"^[a-fA-F\d]{4}:[a-fA-F\d]{2}:[a-fA-F\d]{2}\.[a-fA-F\d]$")

DEVICE_FILE_MAP = {"vendor": "vendor",
                   "device": "product_id"}
DEVICE_FILE_HANDLER = {}
DEVICE_EXPOSED = ["vendor", "device"]

PRODUCT_MAP = {"0x09c4": "PAC_ARRIA10"}

DRIVER_NAME = "intel"


def read_line(filename):
    with open(filename) as f:
        return f.readline().strip()


def is_fpga(p):
    infos = (read_line(os.path.join(p, "vendor")),
             read_line(os.path.join(p, "device")))
    if infos in KNOWN_FPGAS:
        return os.path.realpath(p)


def link_real_path(p):
    return os.path.realpath(
        os.path.join(os.path.dirname(p), os.readlink(p)))


# TODO(s_shogo) This function name should be reconsidered in py3
# env( filter() in py3 returns iterator, not list)
def find_fpgas_by_know_list():
    return filter(
        lambda p: (
            read_line(os.path.join(p, "vendor")),
            read_line(os.path.join(p, "device"))
        ) in KNOWN_FPGAS,
        glob.glob(PCI_DEVICES_PATH_PATTERN))


def get_link_targets(links):
    return map(
        lambda p:
            os.path.realpath(
                os.path.join(os.path.dirname(p), os.readlink(p))),
        links)


def all_fpgas():
    # glob.glob("/sys/class/fpga", "*")
    return set(get_link_targets(find_fpgas_by_know_list())) | set(
        map(lambda p: p.rsplit("/", 2)[0],
            get_link_targets(glob.glob(os.path.join(SYS_FPGA, "*")))))


def all_vf_fpgas():
    return [dev.rsplit("/", 2)[0] for dev in
            glob.glob(os.path.join(SYS_FPGA, "*/device/physfn"))]


def all_pfs_have_vf():
    return list(filter(lambda p: glob.glob(os.path.join(p, "virtfn0")),
                all_fpgas()))


def target_symbolic_map():
    maps = {}
    for f in glob.glob(os.path.join(SYS_FPGA, "*/device")):
        maps[os.path.realpath(f)] = os.path.dirname(f)
    return maps


def bdf_path_map():
    return dict(map(lambda f: (os.path.basename(f), f), all_fpgas()))


def all_vfs_in_pf_fpgas(pf_path):
    return get_link_targets(
        glob.glob(os.path.join(pf_path, "virtfn*")))


def all_pf_fpgas():
    return filter(lambda p: glob.glob(os.path.join(p, "sriov_totalvfs")),
                  all_fpgas())


def is_bdf(bdf):
    return True if BDF_PATTERN.match(bdf) else False


def get_bdf_by_path(path):
    bdf = os.path.basename(path)
    if is_bdf(bdf):
        return bdf
    return os.path.basename(os.readlink(os.path.join(path, "device")))


def get_afu_ids(device_name):
    return map(
        read_line,
        glob.glob(
            os.path.join(
                PCI_DEVICES_PATH_PATTERN, "fpga",
                device_name, "intel-fpga-port.*", "afu_id")
        )
    )


def get_region_ids(device_name):
    return map(
        read_line,
        glob.glob(
            os.path.join(
                SYS_FPGA, device_name,
                "intel-fpga-fme.*", "pr/interface_id")
        )
    )


def get_traits(device_name, product_id, vf=True):
    """Generate traits for devices.
    : param devices_name: name of PF/VF, for example, "intel-fpga-dev.0".
    : param product_id: product id of PF/VF, for example, "0x09c4".
    : param vf: True if device_name is a VF, otherwise False.
    """
    # "CUSTOM_PROGRAMMABLE" not support at present
    traits = []
    if not vf:
        traits.append("CUSTOM_FPGA_INTEL")
        traits.append("CUSTOM_FPGA_INTEL_" + PRODUCT_MAP.get(product_id))
    for i in get_afu_ids(device_name):
        trait = "CUSTOM_FPGA_FUNCTION_ID_INTEL_" + i.upper()
        traits.append(trait)
    for i in get_region_ids(device_name):
        trait = "CUSTOM_FPGA_REGION_INTEL_" + i.upper()
        traits.append(trait)
    return {"traits": traits}


def fpga_device(path):
    infos = {}

    # NOTE "In 3.x, os.path.walk is removed in favor of os.walk."
    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in filenames:
            if filename in DEVICE_EXPOSED:
                key = DEVICE_FILE_MAP.get(filename) or filename
                if key in DEVICE_FILE_HANDLER and callable(
                    DEVICE_FILE_HANDLER(key)):
                    infos[key] = DEVICE_FILE_HANDLER(key)(
                        os.path.join(dirpath, filename))
                else:
                    infos[key] = read_line(os.path.join(dirpath, filename))
    return infos


def fpga_tree():
    def gen_fpga_infos(path, vf=True):
        bdf = get_bdf_by_path(path)
        names = glob.glob1(os.path.join(path, "fpga"), "*")
        fpga = {"type": constants.DEVICE_FPGA,
                "devices": bdf, "stub": True,
                "name": "_".join((socket.gethostname(), bdf))}
        d_info = fpga_device(path)
        fpga.update(d_info)
        if names:
            name = names[0]
            fpga["stub"] = False
            traits = get_traits(name, fpga["product_id"], vf)
            fpga.update(traits)
        fpga["rc"] = constants.RESOURCES["FPGA"]
        return fpga

    devs = []
    pf_has_vf = all_pfs_have_vf()
    for pf in all_pf_fpgas():
        fpga = gen_fpga_infos(pf, False)
        if pf in pf_has_vf:
            # Currently only one region supported.
            fpga["regions"] = []
            # All VFs here belong to one same region.
            vfs = all_vfs_in_pf_fpgas(pf)
            for vf in vfs:
                vf_fpga = gen_fpga_infos(vf, True)
                fpga["regions"].append(vf_fpga)
        devs.append(_generate_driver_device(fpga, pf in pf_has_vf))
    return devs


def _generate_driver_device(fpga, pf_has_vf):
    driver_device_obj = driver_device.DriverDevice()
    driver_device_obj.vendor = fpga["vendor"]
    driver_device_obj.stub = fpga["stub"]
    driver_device_obj.model = fpga.get('model', "miss_model_info")
    driver_device_obj.vendor_board_info = fpga.get('vendor_board_info',
                                                   "miss_vb_info")
    std_board_info = {'product_id': fpga.get('product_id')}
    driver_device_obj.std_board_info = jsonutils.dumps(std_board_info)
    driver_device_obj.type = fpga["type"]
    driver_device_obj.controlpath_id = _generate_controlpath_id(fpga)
    driver_device_obj.deployable_list = _generate_dep_list(fpga, pf_has_vf)
    return driver_device_obj


def _generate_controlpath_id(fpga):
    driver_cpid = driver_controlpath_id.DriverControlPathID()
    driver_cpid.cpid_type = "PCI"
    driver_cpid.cpid_info = utils.pci_str_to_json(fpga["devices"])
    return driver_cpid


def _generate_dep_list(fpga, pf_has_vf):
    driver_dep = driver_deployable.DriverDeployable()
    driver_dep.attribute_list = _generate_attribute_list(fpga)
    driver_dep.attach_handle_list = []
    # pf without sriov enabled.
    if not pf_has_vf:
        driver_dep.num_accelerators = 1
        driver_dep.attach_handle_list = \
            [_generate_attach_handle(fpga)]
        driver_dep.name = fpga["name"]
        driver_dep.driver_name = DRIVER_NAME
    # pf with sriov enabled, may have several regions and several vfs.
    # For now, there is only one region, this maybe improve in next release.
    else:
        driver_dep.num_accelerators = len(fpga["regions"])
        for vf in fpga["regions"]:
            # Only vfs in regions can be attach, no pf.
            driver_dep.attach_handle_list.append(
                _generate_attach_handle(vf))
            driver_dep.name = vf["name"]
            driver_dep.driver_name = DRIVER_NAME
    return [driver_dep]


def _generate_attach_handle(fpga):
    driver_ah = driver_attach_handle.DriverAttachHandle()
    driver_ah.attach_type = constants.AH_TYPE_PCI
    driver_ah.attach_info = utils.pci_str_to_json(fpga["devices"])
    driver_ah.in_use = False
    return driver_ah


def _generate_attribute_list(fpga):
    attr_list = []
    count_pf_traits = 0
    for k, v in fpga.items():
        if k == "rc":
            driver_attr = driver_attribute.DriverAttribute()
            driver_attr.key, driver_attr.value = k, v
            attr_list.append(driver_attr)
        if k == "traits":
            values = fpga.get(k, [])
            for index_pf, val in enumerate(values):
                driver_attr = driver_attribute.DriverAttribute()
                driver_attr.key = "trait" + str(index_pf)
                driver_attr.value = val
                attr_list.append(driver_attr)
                count_pf_traits = index_pf
    vfs = fpga.get('regions', [])
    for vf in vfs:
        for k, values in vf.items():
            if k == "traits":
                for index_vf, val in enumerate(values):
                    driver_attr = driver_attribute.DriverAttribute()
                    driver_attr.key = "trait" + str(index_vf + count_pf_traits)
                    driver_attr.value = val
                    attr_list.append(driver_attr)
    return attr_list
