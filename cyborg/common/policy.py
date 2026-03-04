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
    policy.RuleDefault(
        'cyborg:arq:get_all',
        'rule:default',
        description='Retrieve accelerator request records.',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:arq:get_one',
        'rule:default',
        description='Get an accelerator request record.',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:arq:create',
        'rule:project_member_or_admin',
        description='Create accelerator request records.',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:arq:delete',
        'rule:default',
        description='Delete accelerator request records.',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:arq:update',
        'rule:default',
        description='Update accelerator request records.',
        scope_types=['project'],
    ),
]

device_policies = [
    policy.RuleDefault(
        'cyborg:device:get_one',
        'rule:admin_api',
        description='Show device detail',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:device:get_all',
        'rule:admin_api',
        description='Retrieve all device records',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:device:disable',
        'rule:admin_api',
        description='Disable a device',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:device:enable',
        'rule:admin_api',
        description='Enable a device',
        scope_types=['project'],
    ),
]

deployable_policies = [
    policy.RuleDefault(
        'cyborg:deployable:get_one',
        'rule:admin_api',
        description='Show deployable detail',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:deployable:get_all',
        'rule:admin_api',
        description='Retrieve all deployable records',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:deployable:program',
        'rule:admin_api',
        description='FPGA programming.',
        scope_types=['project'],
    ),
]

attribute_policies = [
    policy.RuleDefault(
        'cyborg:attribute:get_one',
        'rule:admin_api',
        description='Show attribute detail',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:attribute:get_all',
        'rule:admin_api',
        description='Retrieve all attribute records',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:attribute:create',
        'rule:admin_api',
        description='Create an attribute record',
        scope_types=['project'],
    ),
    policy.RuleDefault(
        'cyborg:attribute:delete',
        'rule:admin_api',
        description='Delete attribute records.',
        scope_types=['project'],
    ),
]
