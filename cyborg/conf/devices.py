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


def register_opts(conf):
    conf.register_group(nic_group)
    conf.register_opts(nic_opts, group=nic_group)


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


def list_opts():
    return {nic_group: nic_opts}
