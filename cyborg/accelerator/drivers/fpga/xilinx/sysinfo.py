# Copyright 2021 Inspur, Inc.
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
Cyborg Xilinx FPGA driver implementation.
"""

import re

from oslo_concurrency import processutils
from oslo_log import log as logging
from oslo_serialization import jsonutils

from cyborg.accelerator.common import utils
from cyborg.common import constants
from cyborg.conf import CONF
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_attribute
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device
from cyborg.privsep import sys_admin_pctxt

LOG = logging.getLogger(__name__)

XILINX_FPGA_FLAGS = ["Xilinx Corporation Device",
                     "Processing accelerators"]

XILINX_FPGA_INFO_PATTERN = re.compile(
    r"(?P<pci_addr>[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:"
    r"[0-9a-fA-F]{2}\.[0-9a-fA-F]) "
    r"(?P<controller>.*) [\[].*]: (?P<model>.*) .*"
    r"[\[](?P<vendor_id>[0-9a-fA-F]"
    r"{4}):(?P<product_id>[0-9a-fA-F]{4})].*")

XILINX_PF_MAPS = {"mgmt": "xclmgmt", "user": "xocl"}

VENDOR_MAPS = {"10ee": "xilinx"}


@sys_admin_pctxt.entrypoint
def lspci_privileged(cmd):
    return processutils.execute(*cmd)


def get_pci_devices(pci_flags, vendor_id=None):
    device_for_vendor_out = []
    all_device_out = []
    cmd = ['lspci', '-nnn', '-D']
    lspci_out = lspci_privileged(cmd)[0].split('\n')
    for i in range(len(lspci_out)):
        if all(x in lspci_out[i] for x in pci_flags):
            all_device_out.append(lspci_out[i])
            if vendor_id and vendor_id in lspci_out[i]:
                device_for_vendor_out.append(lspci_out[i])
    return device_for_vendor_out if vendor_id else all_device_out


def _generate_traits(vendor_id, product_id):
    """Generate traits for FPGAs.
    : param vendor_id: vendor_id of FPGA
    : param product_id: product_id of FPGA
    Example FPGA traits:
    {traits:["CUSTOM_FPGA_XILINX", "CUSTOM_FPGA_PRODUCT_ID_5001"]}
    """
    traits = []
    traits.append("CUSTOM_FPGA_" + VENDOR_MAPS.get(vendor_id, "").upper())
    traits.append("CUSTOM_FPGA_PRODUCT_ID_" + product_id.upper())
    return {"traits": traits}


def _get_pf_type(device):
    cmd = ['lspci', '-k', '-s', device]
    result = lspci_privileged(cmd)[0]
    for k, v in XILINX_PF_MAPS.items():
        if v in result:
            return k


def _combine_device_by_pci_func(pci_devices):
    fpga_devices = []
    for pci_dev in pci_devices:
        m = XILINX_FPGA_INFO_PATTERN.match(pci_dev)
        if m:
            pci_dict = m.groupdict()
            LOG.debug('Xilinx fpga pci device in dict: %s', pci_dict)
            # 0000:3b:00.0/1
            is_existed = False
            new_addr = pci_dict.get('pci_addr')
            for fpga in fpga_devices:
                existed_addr = fpga.get('pci_addr')[0]
                # compare domain:bus:slot
                if existed_addr and \
                    new_addr.split('.')[0] == existed_addr.split('.')[0]:
                    fpga.update({'pci_addr': [existed_addr, new_addr]})
                    is_existed = True
            if not is_existed:
                traits = _generate_traits(pci_dict["vendor_id"],
                                          pci_dict["product_id"])
                pci_dict["rc"] = constants.RESOURCES["FPGA"]
                pci_dict.update(traits)
                pci_dict.update({'pci_addr': [new_addr]})
                fpga_devices.append(pci_dict)
    return fpga_devices


def _generate_controlpath_id(fpga):
    driver_cpid = driver_controlpath_id.DriverControlPathID()
    driver_cpid.cpid_type = "PCI"
    driver_cpid.cpid_info = utils.pci_str_to_json(fpga['pci_addr'][0])
    return driver_cpid


def _generate_dep_list(fpga):
    dep_list = []
    driver_dep = driver_deployable.DriverDeployable()
    driver_dep.attribute_list = _generate_attribute_list(fpga)
    driver_dep.attach_handle_list = []
    driver_dep.name = CONF.host + '_' + fpga["pci_addr"][0]
    driver_dep.driver_name = VENDOR_MAPS.get(fpga["vendor_id"], '').upper()
    driver_dep.num_accelerators = 1
    driver_dep.attach_handle_list = _generate_attach_handle(fpga)
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
    driver_ahs = []
    for addr in fpga.get('pci_addr'):
        driver_ah = driver_attach_handle.DriverAttachHandle()
        driver_ah.attach_type = constants.AH_TYPE_PCI
        driver_ah.attach_info = utils.pci_str_to_json(addr)
        driver_ah.in_use = False
        driver_ahs.append(driver_ah)
    return driver_ahs


def fpga_tree():
    fpga_list = []
    fpga_pci_devices = get_pci_devices(XILINX_FPGA_FLAGS)
    LOG.debug("Xilinx fpga devices from lspci: %s", fpga_pci_devices)
    # In the return pci devices, mgmt pf and user pf are two entries.
    # Now only when binding both to vm, end user can program it.
    # So combine these two entries into one device.
    for fpga in _combine_device_by_pci_func(fpga_pci_devices):
        driver_device_obj = driver_device.DriverDevice()
        driver_device_obj.vendor = fpga["vendor_id"]
        driver_device_obj.model = fpga.get('model', 'miss model info')
        std_board_info = {'product_id': fpga.get('product_id'),
                          'controller': fpga.get('controller')}
        vendor_board_info = {
            'vendor_info': fpga.get('vendor_info', 'fpga_vb_info')}
        driver_device_obj.std_board_info = jsonutils.dumps(std_board_info)
        driver_device_obj.vendor_board_info = \
            jsonutils.dumps(vendor_board_info)
        driver_device_obj.type = constants.DEVICE_FPGA
        driver_device_obj.stub = fpga.get('stub', False)
        driver_device_obj.controlpath_id = _generate_controlpath_id(fpga)
        driver_device_obj.deployable_list = _generate_dep_list(fpga)
        fpga_list.append(driver_device_obj)
    return fpga_list
