# Copyright 2017 Huawei Technologies Co.,LTD.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


"""legacy old_policies, the following old_policies will be removed once
   new policies are implemented.
"""
from oslo_policy import policy
# NOTE: to follow policy-in-code spec, we define defaults for
#       the granular policies in code, rather than in policy.yaml.
#       All of these may be overridden by configuration, but we can
#       depend on their existence throughout the code.

accelerator_request_policies = [
    policy.RuleDefault('cyborg:arq:get_all',
                       'rule:default',
                       description='Retrieve accelerator request records.'),
    policy.RuleDefault('cyborg:arq:get_one',
                       'rule:default',
                       description='Get an accelerator request record.'),
    policy.RuleDefault('cyborg:arq:create',
                       'rule:allow',
                       description='Create accelerator request records.'),
    policy.RuleDefault('cyborg:arq:delete',
                       'rule:default',
                       description='Delete accelerator request records.'),
    policy.RuleDefault('cyborg:arq:update',
                       'rule:default',
                       description='Update accelerator request records.'),
]

device_policies = [
    policy.RuleDefault('cyborg:device:get_one',
                       'rule:allow',
                       description='Show device detail'),
    policy.RuleDefault('cyborg:device:get_all',
                       'rule:allow',
                       description='Retrieve all device records'),
]

deployable_policies = [
    policy.RuleDefault('cyborg:deployable:get_one',
                       'rule:allow',
                       description='Show deployable detail'),
    policy.RuleDefault('cyborg:deployable:get_all',
                       'rule:allow',
                       description='Retrieve all deployable records'),
    policy.RuleDefault('cyborg:deployable:program',
                       'rule:allow',
                       description='FPGA programming.'),
]

fpga_policies = [
    policy.RuleDefault('cyborg:fpga:get_one',
                       'rule:allow',
                       description='Show fpga detail'),
    policy.RuleDefault('cyborg:fpga:get_all',
                       'rule:allow',
                       description='Retrieve all fpga records'),
    policy.RuleDefault('cyborg:fpga:update',
                       'rule:allow',
                       description='Update fpga records'),
]
