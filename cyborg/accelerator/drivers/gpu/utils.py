# Modifications Copyright (C) 2021 ZTE Corporation
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
Utils for GPU driver.
"""
from oslo_concurrency import processutils
from oslo_log import log as logging

import re

import cyborg.common.exception as exception
import cyborg.conf
import cyborg.privsep

LOG = logging.getLogger(__name__)

GPU_FLAGS = ["VGA compatible controller", "3D controller"]
GPU_INFO_PATTERN = re.compile(r"(?P<devices>[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:"
                              r"[0-9a-fA-F]{2}\.[0-9a-fA-F]) "
                              r"(?P<controller>.*) [\[].*]: (?P<model>.*) .*"
                              r"[\[](?P<vendor_id>[0-9a-fA-F]"
                              r"{4}):(?P<product_id>[0-9a-fA-F]{4})].*")

VENDOR_MAPS = {"10de": "nvidia", "102b": "matrox"}
PRODUCT_ID_MAPS = {"1eb8": "T4", "15f7": "P100_PCIE_12GB"}


@cyborg.privsep.sys_admin_pctxt.entrypoint
def lspci_privileged():
    cmd = ['lspci', '-nnn', '-D']
    return processutils.execute(*cmd)


@cyborg.privsep.sys_admin_pctxt.entrypoint
def create_mdev_privileged(pci_addr, mdev_type, ah_uuid):
    """Instantiate a mediated device."""
    if ah_uuid is None:
        raise exception.AttachHandleUUIDNeeded()
    fpath = '/sys/class/mdev_bus/{0}/mdev_supported_types/{1}/create'
    fpath = fpath.format(pci_addr, mdev_type)
    with open(fpath, 'w') as f:
        f.write(ah_uuid)
    return ah_uuid


@cyborg.privsep.sys_admin_pctxt.entrypoint
def remove_mdev_privileged(physical_device, mdev_type, medv_uuid):
    fpath = ('/sys/class/mdev_bus/{0}/mdev_supported_types/'
             '{1}/devices/{2}/remove')
    fpath = fpath.format(physical_device, mdev_type, medv_uuid)
    with open(fpath, 'w') as f:
        f.write("1")


def get_pci_devices(pci_flags, vendor_id=None):
    device_for_vendor_out = []
    all_device_out = []
    lspci_out = lspci_privileged()[0].split('\n')
    for pci in lspci_out:
        if any(x in pci for x in pci_flags):
            all_device_out.append(pci)
            if vendor_id and vendor_id in pci:
                device_for_vendor_out.append(pci)
    return device_for_vendor_out if vendor_id else all_device_out


def discover_vendors():
    vendors = set()
    gpus = get_pci_devices(GPU_FLAGS)
    for gpu in gpus:
        m = GPU_INFO_PATTERN.match(gpu)
        if m:
            vendor_id = m.groupdict().get("vendor_id")
            vendors.add(vendor_id)
    return vendors
