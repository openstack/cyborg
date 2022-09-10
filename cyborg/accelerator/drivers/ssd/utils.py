# Copyright 2020 Inspur Electronic Information Industry Co.,LTD.
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
Utils for SSD driver.
"""

from oslo_concurrency import processutils
from oslo_log import log as logging
from oslo_serialization import jsonutils

import re

from cyborg.accelerator.common import utils
from cyborg.common import constants
from cyborg.conf import CONF
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_attribute
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device
import cyborg.privsep

LOG = logging.getLogger(__name__)

SSD_FLAGS = ["Non-Volatile memory controller"]
SSD_INFO_PATTERN = re.compile(r"(?P<devices>[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:"
                              r"[0-9a-fA-F]{2}\.[0-9a-fA-F]) "
                              r"(?P<controller>.*) [\[].*]: (?P<model>.*) .*"
                              r"[\[](?P<vendor_id>[0-9a-fA-F]"
                              r"{4}):(?P<product_id>[0-9a-fA-F]{4})].*")

VENDOR_MAPS = utils.get_vendor_maps()


@cyborg.privsep.sys_admin_pctxt.entrypoint
def lspci_privileged():
    cmd = ['lspci', '-nn', '-D']
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
    """Generate traits for SSDs.
    : param vendor_id: vendor_id of SSD, eg."1bd4"
    : param product_id: product_id of SSD, eg."1003".
    Example SSD traits:
    {traits:["CUSTOM_SSD_INSPUR", "CUSTOM_SSD_PRODUCT_ID_1003"]}
    """
    traits = []
    traits.append("CUSTOM_SSD_" + VENDOR_MAPS.get(vendor_id, "").upper())
    traits.append("CUSTOM_SSD_PRODUCT_ID_" + product_id.upper())
    return {"traits": traits}


def discover_vendors():
    vendors = set()
    ssds = get_pci_devices(SSD_FLAGS)
    for ssd in ssds:
        m = SSD_INFO_PATTERN.match(ssd)
        if m:
            vendor_id = m.groupdict().get("vendor_id")
            vendors.add(vendor_id)
    return vendors


def discover_ssds(vendor_id=None):
    ssd_list = []
    ssds = get_pci_devices(SSD_FLAGS, vendor_id)
    for ssd in ssds:
        m = SSD_INFO_PATTERN.match(ssd)
        if m:
            ssd_dict = m.groupdict()
            ssd_dict['hostname'] = CONF.host
            # generate traits info
            traits = get_traits(ssd_dict["vendor_id"], ssd_dict["product_id"])
            ssd_dict["rc"] = constants.RESOURCES["SSD"]
            ssd_dict.update(traits)
            ssd_list.append(_generate_driver_device(ssd_dict))
    return ssd_list


def _generate_driver_device(ssd):
    driver_device_obj = driver_device.DriverDevice()
    driver_device_obj.vendor = ssd["vendor_id"]
    driver_device_obj.model = ssd.get('model', 'miss model info')
    std_board_info = {'product_id': ssd.get('product_id'),
                      'controller': ssd.get('controller')}
    vendor_board_info = {'vendor_info': ssd.get('vendor_info', 'ssd_vb_info')}
    driver_device_obj.std_board_info = jsonutils.dumps(std_board_info)
    driver_device_obj.vendor_board_info = jsonutils.dumps(vendor_board_info)
    driver_device_obj.type = constants.DEVICE_SSD
    driver_device_obj.stub = ssd.get('stub', False)
    driver_device_obj.controlpath_id = _generate_controlpath_id(ssd)
    driver_device_obj.deployable_list = _generate_dep_list(ssd)
    return driver_device_obj


def _generate_controlpath_id(ssd):
    driver_cpid = driver_controlpath_id.DriverControlPathID()
    # NOTE: SSDs , they all report "PCI" as
    # their cpid_type, while attach_handle_type of them are different.
    driver_cpid.cpid_type = "PCI"
    driver_cpid.cpid_info = utils.pci_str_to_json(ssd["devices"])
    return driver_cpid


def _generate_dep_list(ssd):
    dep_list = []
    driver_dep = driver_deployable.DriverDeployable()
    driver_dep.attribute_list = _generate_attribute_list(ssd)
    driver_dep.attach_handle_list = []
    # NOTE(wenping) Now simply named as <Compute_hostname>_<Device_address>
    # once cyborg needs to support SSD devices discovered from a baremetal
    # node, we might need to support more formats.
    driver_dep.name = ssd.get('hostname', '') + '_' + ssd["devices"]
    driver_dep.driver_name = VENDOR_MAPS.get(ssd["vendor_id"], '').upper()
    # driver_dep.num_accelerators for SSD is 1
    driver_dep.num_accelerators = 1
    driver_dep.attach_handle_list = [_generate_attach_handle(ssd)]
    dep_list.append(driver_dep)
    return dep_list


def _generate_attach_handle(ssd):
    driver_ah = driver_attach_handle.DriverAttachHandle()
    if ssd["rc"] == "CUSTOM_SSD":
        driver_ah.attach_type = constants.AH_TYPE_PCI
    else:
        driver_ah.attach_type = constants.AH_TYPE_MDEV
    driver_ah.in_use = False
    driver_ah.attach_info = utils.pci_str_to_json(ssd["devices"])
    return driver_ah


def _generate_attribute_list(ssd):
    attr_list = []
    for k, v in ssd.items():
        if k == "rc":
            driver_attr = driver_attribute.DriverAttribute()
            driver_attr.key, driver_attr.value = k, v
            attr_list.append(driver_attr)
        if k == "traits":
            values = ssd.get(k, [])
            for index, val in enumerate(values):
                driver_attr = driver_attribute.DriverAttribute(
                    key="trait" + str(index), value=val)
                attr_list.append(driver_attr)
    return attr_list
