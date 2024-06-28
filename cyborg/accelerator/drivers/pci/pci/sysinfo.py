# Copyright 2024 Inspur.
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
Cyborg PCI driver implementation.
"""
from oslo_log import log as logging
from oslo_serialization import jsonutils

from cyborg.accelerator.common import utils
from cyborg.accelerator.drivers.pci import utils as pci_utils
from cyborg.accelerator.drivers.pci import whitelist
from cyborg.common import constants
import cyborg.conf
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_attribute
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device

LOG = logging.getLogger(__name__)
CONF = cyborg.conf.CONF


def _get_traits(vendor_id, product_id):
    """Generate traits for PCIs.
    : param vendor_id: vendor_id of PCI, eg."10de"
    : param product_id: product_id of PCI, eg."1eb8".

    Example PGPU traits:
    {traits:["OWNER_CYBORG", "CUSTOM_PCI_1EB8"]}
    """
    vendor_name = pci_utils.VENDOR_MAPS.get(vendor_id).upper()
    traits = ["CUSTOM_PCI_" + vendor_name]
    # PCIE trait
    product_trait = "_".join(('CUSTOM_PCI_PRODUCT_ID', product_id.upper()))
    traits.append(product_trait)
    return {"traits": traits}


def _generate_attribute_list(pci):
    attr_list = []
    index = 0
    for k, v in pci.items():
        if k == "rc":
            driver_attr = driver_attribute.DriverAttribute()
            driver_attr.key, driver_attr.value = k, v
            attr_list.append(driver_attr)
        if k == "traits":
            values = pci.get(k, [])
            for val in values:
                driver_attr = driver_attribute.DriverAttribute(
                    key="trait" + str(index), value=val)
                index = index + 1
                attr_list.append(driver_attr)
    return attr_list


def _generate_attach_handle(pci):
    driver_ah = driver_attach_handle.DriverAttachHandle()
    driver_ah.in_use = False
    driver_ah.attach_type = constants.AH_TYPE_PCI
    driver_ah.attach_info = utils.pci_str_to_json(pci["devices"])
    return driver_ah


def _generate_dep_list(pci):
    dep_list = []
    driver_dep = driver_deployable.DriverDeployable()
    driver_dep.attribute_list = _generate_attribute_list(pci)
    driver_dep.attach_handle_list = []
    # NOTE(wangzhh): The name of deployable should be unique, its format is
    # under disscussion, may looks like
    # <ComputeNodeName>_<NumaNodeName>_<CyborgName>_<NumInHost>
    # NOTE(yumeng) Since Wallaby release, the deplpyable_name is named as
    # <Compute_hostname>_<Device_address>
    driver_dep.name = pci.get('hostname', '') + '_' + pci["devices"]
    driver_dep.driver_name = \
        pci_utils.VENDOR_MAPS.get(pci["vendor_id"]).upper()
    driver_dep.num_accelerators = 1
    driver_dep.attach_handle_list = [_generate_attach_handle(pci)]
    dep_list.append(driver_dep)
    return dep_list, driver_dep.num_accelerators


def _generate_controlpath_id(pci):
    driver_cpid = driver_controlpath_id.DriverControlPathID()
    driver_cpid.cpid_type = "PCI"
    driver_cpid.cpid_info = utils.pci_str_to_json(pci["devices"])
    return driver_cpid


def _generate_driver_device(pci):
    driver_device_obj = driver_device.DriverDevice()
    driver_device_obj.vendor = pci['vendor_id']
    driver_device_obj.model = pci['product_id']
    std_board_info = {'product_id': pci.get('product_id'),
                      'controller': pci.get('controller'),
                      }
    driver_device_obj.std_board_info = jsonutils.dumps(std_board_info)
    driver_device_obj.type = constants.DEVICE_GPU
    driver_device_obj.stub = pci.get('stub', False)
    driver_device_obj.controlpath_id = _generate_controlpath_id(pci)
    driver_device_obj.deployable_list, ais = _generate_dep_list(pci)
    driver_device_obj.vendor_board_info = pci.get('vendor_board_info',
                                                  "miss_vb_info")
    return driver_device_obj


def _discover_pcis():
    cyborg.conf.devices.register_dynamic_opts(CONF)
    # discover pci devices by "lspci"
    pci_list = []
    pcis = pci_utils.get_pci_devices()
    LOG.info('pcis:%s', pcis)
    # report trait,rc and generate driver object
    dev_filter = whitelist.Whitelist(CONF.pci.passthrough_whitelist)
    for pci in pcis:
        m = dev_filter.device_assignable(pci)
        if m:
            pci_dict = m.groupdict()
            # get hostname for deployable_name usage
            pci_dict['hostname'] = CONF.host
            pci_dict["rc"] = constants.RESOURCES["PCI"]
            traits = _get_traits(pci_dict["vendor_id"],
                                 pci_dict["product_id"])
            pci_dict.update(traits)
            pci_list.append(_generate_driver_device(pci_dict))
    LOG.info('pci_list:%s', pci_list)
    return pci_list


def discover():
    devs = _discover_pcis()
    return devs
