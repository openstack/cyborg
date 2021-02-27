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

from oslo_config import cfg


nic_group = cfg.OptGroup(
    name='nic_devices',
    title='nic device ID options',
    help="""This is used to config specific nic devices.
    """)

nic_opts = [
    cfg.ListOpt('enabled_nic_types',
                default=[],
                help=" ")
]

gpu_group = cfg.OptGroup(
    name='gpu_devices',
    title='virtual gpu options',
    help="""This is used to config vGPU types for nvidia GPU devices.
    """)

vgpu_opts = [
    cfg.ListOpt('enabled_vgpu_types',
                default=[],
                help="""
The vGPU types enabled in the compute node.

Cyborg supports multiple vGPU types in one host. Usually, a single physical
GPU can only set one vgpu type. Some pGPUs (e.g. NVIDIA GRID K1) support
multiple vGPU types.

If more than one single vGPU type are provided, then for each
*vGPU type*, you must add an additional section ``[vgpu_$(VGPU_TYPE)]`` with
a single configuration option ``device_addresses`` to assign this type to
the target physical GPU(s). PGPUs should be configured explictly now, we will
improve this after we implement the enable/disable interface.

If the same PCI address is provided for two different types, cyborg-agent will
return an InvalidGPUConfig exception at restart.

An example is as the following::

    [gpu_devices]
    enabled_vgpu_types = nvidia-35, nvidia-36

    [vgpu_nvidia-35]
    device_addresses = 0000:84:00.0,0000:85:00.0

    [vgpu_nvidia-36]
    device_addresses = 0000:86:00.0

""")
]


def register_opts(conf):
    conf.register_group(nic_group)
    conf.register_opts(nic_opts, group=nic_group)
    conf.register_group(gpu_group)
    conf.register_opts(vgpu_opts, group=gpu_group)


def register_dynamic_opts(conf):
    """Register dynamically-generated options and groups.

    This must be called by the service that wishes to use the options **after**
    the initial configuration has been loaded.
    """
    opts = [
        cfg.ListOpt('physical_device_mappings', default=[],
                    item_type=cfg.types.String()),
        cfg.ListOpt('function_device_mappings', default=[],
                    item_type=cfg.types.String()),
    ]

    # Register the '[nic_type]/physical_device_mappings' and
    # '[nic_type]/function_device_mappings' opts, implicitly
    # registering the '[nic_type]' groups in the process
    for nic_type in conf.nic_devices.enabled_nic_types:
        conf.register_opts(opts, group=nic_type)
    # Register the '[vgpu_$(VGPU_TYPE)]/device_addresses' opts, implicitly
    # registering the '[vgpu_$(VGPU_TYPE)]' groups in the process
    opt = cfg.ListOpt('device_addresses', default=[],
                      item_type=cfg.types.String())
    for vgpu_type in conf.gpu_devices.enabled_vgpu_types:
        conf.register_opt(opt, group='vgpu_%s' % vgpu_type)


def list_opts():
    return {nic_group: nic_opts, gpu_group: vgpu_opts}
