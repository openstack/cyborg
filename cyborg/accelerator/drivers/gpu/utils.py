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

from oslo_log import log as logging

import cyborg.common.exception as exception
import cyborg.conf
import cyborg.privsep

from cyborg.accelerator.common import utils


LOG = logging.getLogger(__name__)

GPU_FLAGS = ["VGA compatible controller", "3D controller"]

VENDOR_MAPS = {"10de": "nvidia", "102b": "matrox"}
PRODUCT_ID_MAPS = {"1eb8": "T4", "15f7": "P100_PCIE_12GB"}


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
    fpath = (
        '/sys/class/mdev_bus/{0}/mdev_supported_types/{1}/devices/{2}/remove'
    )
    fpath = fpath.format(physical_device, mdev_type, medv_uuid)
    with open(fpath, 'w') as f:
        f.write("1")


def discover_vendors():
    vendors = set()
    gpus = (
        dev
        for dev in utils.get_pci_devices()
        if any(flag in dev["raw_line"] for flag in GPU_FLAGS)
    )
    for gpu in gpus:
        vendor_id = gpu.get("vendor_id")
        vendors.add(vendor_id)
    return vendors
