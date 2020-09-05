# Copyright 2020 Inspur, Inc.
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
Cyborg Inspur FPGA driver implementation.
"""

import re

from oslo_concurrency import processutils
from oslo_serialization import jsonutils

from cyborg.accelerator.common import utils
from cyborg.common import constants
from cyborg.conf import CONF
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_attribute
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device
import cyborg.privsep

INSPUR_FPGA_FLAGS = ["Inspur Electronic Information Industry Co., Ltd.",
                     "Processing accelerators"]
INSPUR_FPGA_INFO_PATTERN = re.compile(
    r"(?P<devices>[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:"
    r"[0-9a-fA-F]{2}\.[0-9a-fA-F]) "
    r"(?P<controller>.*) [\[].*]: (?P<name>.*) .*"
    r"[\[](?P<vendor_id>[0-9a-fA-F]"
    r"{4}):(?P<product_id>[0-9a-fA-F]{4})].*")

VENDOR_MAPS = {"1bd4": "inspur"}


@cyborg.privsep.sys_admin_pctxt.entrypoint
def lspci_privileged():
    cmd = ['lspci', '-nnn', '-D']
    return processutils.execute(*cmd)


def get_pci_devices(pci_flags, vendor_id=None):
    device_for_vendor_out = []
    all_device_out = []
    lspci_out = lspci_privileged()[0].split('\n')
    for i in range(len(lspci_out)):
        if any(x in lspci_out[i] for x in pci_flags):
            all_device_out.append(lspci_out[i])
            if vendor_id and vendor_id in lspci_out[i]:
                device_for_vendor_out.append(lspci_out[i])
    return device_for_vendor_out if vendor_id else all_device_out


def get_traits(vendor_id, product_id):
    """Generate traits for FPGAs.
    : param vendor_id: vendor_id of FPGA, eg."1bd4"
    : param product_id: product_id of FPGA, eg."a115".
    Example FPGA traits:
    {traits:["CUSTOM_FPGA_INSPUR", "CUSTOM_FPGA_PRODUCT_ID_A115"]}
    """
    traits = []
    traits.append("CUSTOM_FPGA_" + VENDOR_MAPS.get(vendor_id, "").upper())
    traits.append("CUSTOM_FPGA_PRODUCT_ID_" + product_id.upper())
    # TODO(wenping) Currently we don't support program by Cyborg. The operator
    # can bind Inspur FPGA card to guest and then use it in guest. So the BSP
    # data reported is ignored here now.
    return {"traits": traits}


def fpga_tree():
    fpga_list = []
    fpgas = get_pci_devices(INSPUR_FPGA_FLAGS)
    for fpga in fpgas:
        m = INSPUR_FPGA_INFO_PATTERN.match(fpga)
        if m:
            fpga_dict = m.groupdict()
            # generate traits info
            traits = get_traits(
                fpga_dict["vendor_id"], fpga_dict["product_id"])
            fpga_dict["rc"] = constants.RESOURCES["FPGA"]
            fpga_dict.update(traits)
            fpga_list.append(_generate_driver_device(fpga_dict))
    return fpga_list


def _generate_driver_device(fpga):
    driver_device_obj = driver_device.DriverDevice()
    driver_device_obj.vendor = fpga["vendor_id"]
    driver_device_obj.model = fpga.get('model', 'miss model info')
    std_board_info = {'product_id': fpga.get('product_id', None),
                      'controller': fpga.get('controller', None)}
    vendor_board_info = {
        'vendor_info': fpga.get('vendor_info', 'fpga_vb_info')}
    driver_device_obj.std_board_info = jsonutils.dumps(std_board_info)
    driver_device_obj.vendor_board_info = jsonutils.dumps(vendor_board_info)
    driver_device_obj.type = constants.DEVICE_FPGA
    driver_device_obj.stub = fpga.get('stub', False)
    driver_device_obj.controlpath_id = _generate_controlpath_id(fpga)
    driver_device_obj.deployable_list = _generate_dep_list(fpga)
    return driver_device_obj


def _generate_controlpath_id(fpga):
    driver_cpid = driver_controlpath_id.DriverControlPathID()
    driver_cpid.cpid_type = "PCI"
    driver_cpid.cpid_info = utils.pci_str_to_json(fpga["devices"])
    return driver_cpid


def _generate_dep_list(fpga):
    dep_list = []
    driver_dep = driver_deployable.DriverDeployable()
    driver_dep.attribute_list = _generate_attribute_list(fpga)
    driver_dep.attach_handle_list = []
    # NOTE(wenping) Now simply named as <Compute_hostname>_<Device_address>
    # once cyborg needs to support Inspur FPGA devices discovered from a
    # baremetal node, we might need to support more formats.
    driver_dep.name = CONF.host + '_' + fpga["devices"]
    driver_dep.driver_name = VENDOR_MAPS.get(fpga["vendor_id"]).upper()
    driver_dep.num_accelerators = 1
    driver_dep.attach_handle_list = [_generate_attach_handle(fpga)]
    dep_list.append(driver_dep)
    return dep_list


def _generate_attribute_list(fpga):
    attr_list = []
    for k, v in fpga.items():
        if k == "rc":
            driver_attr = driver_attribute.DriverAttribute()
            driver_attr.key, driver_attr.value = k, v
            attr_list.append(driver_attr)
        if k == "traits":
            values = fpga.get(k, [])
            for index, val in enumerate(values):
                driver_attr = driver_attribute.DriverAttribute(
                    key="trait" + str(index), value=val)
                attr_list.append(driver_attr)
    return attr_list


def _generate_attach_handle(fpga):
    driver_ah = driver_attach_handle.DriverAttachHandle()
    driver_ah.attach_type = constants.AH_TYPE_PCI
    driver_ah.attach_info = utils.pci_str_to_json(fpga["devices"])
    driver_ah.in_use = False
    return driver_ah
