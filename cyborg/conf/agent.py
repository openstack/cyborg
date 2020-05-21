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

from oslo_config import cfg

from cyborg.common.i18n import _


opts = [
    cfg.ListOpt('enabled_drivers',
                default=[],
                help=_('The accelerator drivers enabled on this agent. Such '
                       'as intel_fpga_driver, inspur_fpga_driver,'
                       'nvidia_gpu_driver, etc.')),
]

opt_group = cfg.OptGroup(name='agent',
                         title='Options for the cyborg-agent service')


AGENT_OPTS = (opts)


def register_opts(conf):
    conf.register_group(opt_group)
    conf.register_opts(opts, group=opt_group)


def list_opts():
    return {
        opt_group: AGENT_OPTS
    }
