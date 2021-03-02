# Copyright 2019 Intel, Inc.
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

import collections
import os

from oslo_serialization import jsonutils

from cyborg.common import exception


def pci_str_to_json(pci_address, physnet=None):
    dbs, func = pci_address.split('.')
    domain, bus, slot = dbs.split(':')
    keys = ["domain", "bus", "device", "function"]
    values = [domain, bus, slot, func]
    if physnet:
        keys.append("physical_network")
        values.append(physnet)
    bdf_dict = dict(zip(keys, values))
    ordered_dict = collections.OrderedDict(sorted(bdf_dict.items()))
    bdf_json = jsonutils.dumps(ordered_dict)
    return bdf_json


def _get_sysfs_netdev_path(pci_addr, vf_interface=False):
    """Get the sysfs path based on the PCI address of the device.
    Assumes a networking device - will not check for the existence of the path.
    :param pci_addr: the pci addresee of the device(PF or VF).
    :param vf_interface: True if the pci_addr is a VF,
        False if the pci_addr is a PF.
    :returns: the sysfs path corresponds to the pci_addr.
    """
    if vf_interface:
        return "/sys/bus/pci/devices/%s/physfn/net" % pci_addr
    return "/sys/bus/pci/devices/%s/net" % pci_addr


def get_ifname_by_pci_address(pci_addr, vf_interface=False):
    """Get the interface name based on the pci address.
    The returned interface name is either the parent PF's or that of the PF
    itself based on the argument of vf_interface.
    :param pci_addr: the pci address of the device(PF or VF)
    :param vf_interface: True if the pci_addr is a VF,
        False if the pci_addr is a PF.
    :returns: the interface name corresponds to the pci_addr.
    """
    dev_path = _get_sysfs_netdev_path(pci_addr, vf_interface)
    try:
        dev_info = os.listdir(dev_path)
        return dev_info.pop()
    except Exception:
        raise exception.PciDeviceNotFoundById(id=pci_addr)


def parse_mappings(mapping_list):
    """Parse mapping devices list

    parses mapping device list in the form:
    physnet:pci_dev_1,pci_dev_2 or
    function:pci_dev_1,pci_dev_2
    :param mapping_list: list of string pairs in "key:value" format
                    the key part represents the physnet or function name
                    the value part is a list of device name separated by ","
    :returns: a dict of valid fields.
    """
    mapping = {}
    for dev_mapping in mapping_list:
        try:
            physnet_or_function, devices = dev_mapping.split(":", 1)
        except ValueError:
            raise ValueError(("Invalid mapping: '%s'") % dev_mapping)
        physnet_or_function = physnet_or_function.strip()
        if not physnet_or_function:
            raise ValueError(("Missing key in mapping: '%s'") % dev_mapping)
        if physnet_or_function in mapping:
            raise ValueError(
                ("Key %(physnet_or_function)s in mapping: %(mapping)s "
                 "not unique") % {'physnet_or_function': physnet_or_function,
                                  'mapping': dev_mapping})
        mapping[physnet_or_function] = set(dev.strip() for dev in
                                           devices.split("|") if dev.strip())
    return mapping


def get_vendor_maps():
    """The data is based on http://pci-ids.ucw.cz/read/PC/

    :return: vendor maps dict
    """
    return {"10de": "nvidia",
            "102b": "matrox",
            "1bd4": "inspur",
            "8086": "intel",
            "1099": "samsung",
            "1cf2": "zte"
            }
