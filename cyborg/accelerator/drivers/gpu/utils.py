# Copyright 2018 Beijing Lenovo Software Ltd.
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
Utils for GPU driver.
"""
from oslo_concurrency import processutils
from oslo_log import log as logging
from oslo_serialization import jsonutils

import re

from cyborg.accelerator.common import utils
from cyborg.common import constants
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device
import cyborg.privsep

LOG = logging.getLogger(__name__)

GPU_FLAGS = ["VGA compatible controller", "3D controller"]
GPU_INFO_PATTERN = re.compile("(?P<devices>[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:"
                              "[0-9a-fA-F]{2}\.[0-9a-fA-F]) "
                              "(?P<controller>.*) [\[].*]: (?P<name>.*) .*"
                              "[\[](?P<vendor_id>[0-9a-fA-F]"
                              "{4}):(?P<product_id>[0-9a-fA-F]{4})].*")

# NOTE(wangzhh): The implementation of current release doesn't support virtual
# GPU.


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


def discover_vendors():
    vendors = set()
    gpus = get_pci_devices(GPU_FLAGS)
    for gpu in gpus:
        m = GPU_INFO_PATTERN.match(gpu)
        if m:
            vendor_id = m.groupdict().get("vendor_id")
            vendors.add(vendor_id)
    return vendors


def discover_gpus(vendor_id=None):
    gpu_list = []
    gpus = get_pci_devices(GPU_FLAGS, vendor_id)
    for gpu in gpus:
        m = GPU_INFO_PATTERN.match(gpu)
        if m:
            gpu_dict = m.groupdict()
            gpu_list.append(_generate_driver_device(gpu_dict))
    return gpu_list


def _generate_driver_device(gpu):
    driver_device_obj = driver_device.DriverDevice()
    driver_device_obj.vendor = gpu["vendor_id"]
    driver_device_obj.model = gpu.get('model', 'miss model info')
    std_board_info = {'product_id': gpu.get('product_id', None),
                      'controller': gpu.get('controller', None)}
    driver_device_obj.std_board_info = jsonutils.dumps(std_board_info)
    driver_device_obj.type = constants.DEVICE_GPU
    driver_device_obj.stub = gpu.get('stub', False)
    driver_device_obj.controlpath_id = _generate_controlpath_id(gpu)
    driver_device_obj.deployable_list = _generate_dep_list(gpu)
    return driver_device_obj


def _generate_controlpath_id(gpu):
    driver_cpid = driver_controlpath_id.DriverControlPathID()
    driver_cpid.cpid_type = "PCI"
    driver_cpid.cpid_info = utils.pci_str_to_json(gpu["devices"])
    return driver_cpid


def _generate_dep_list(gpu):
    dep_list = []
    driver_dep = driver_deployable.DriverDeployable()
    driver_dep.attach_handle_list = []
    # NOTE(wangzhh): The name of deployable should be unique, its format is
    # under disscussion, may looks like
    # <ComputeNodeName>_<NumaNodeName>_<CyborgName>_<NumInHost>, now simply
    # named <Device_name>_<Device_address>
    driver_dep.name = gpu.get('name', '') + '_' + gpu["devices"]
    driver_dep.num_accelerators = 1
    driver_dep.attach_handle_list = \
        [_generate_attach_handle(gpu)]
    dep_list.append(driver_dep)
    return dep_list


def _generate_attach_handle(gpu):
    driver_ah = driver_attach_handle.DriverAttachHandle()
    driver_ah.attach_type = constants.AH_TYPE_PCI
    driver_ah.in_use = False
    driver_ah.attach_info = utils.pci_str_to_json(gpu["devices"])
    return driver_ah
