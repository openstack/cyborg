# Copyright 2020 ZTE Corporation.
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


from oslo_log import versionutils
from oslo_policy import policy

from cyborg.policies import base


# NOTE(yumeng)During the Policy-default-refresh work, the old device_profile
# policies will be marked as deprecated device_profile policies.
# To ensure API works fine with both old policies and new policies, we set
# ``cyborg.conf [oslo_policy] enforce_scope = False`` by default. With this,
# policy authorization check will pass those who comply with either new policy
# rules or old policy rules by invoking oslo_policy.policy.OrCheck
# (REF:https://github.com/openstack/oslo.policy/blob/cab28649c689067970a51a2f9b329bdd6a0f0501/oslo_policy/policy.py#L726)
# And once we move to new defaults only world, we will set
# ``cyborg.conf [oslo_policy] enforce_scope = True`` by default, at which time
# we can totally remove these deprecated device_profile policies from code.
deprecated_get_all = policy.DeprecatedRule(
    name='cyborg:device_profile:get_all',
    check_str=base.deprecated_default)
deprecated_get_one = policy.DeprecatedRule(
    name='cyborg:device_profile:get_one',
    check_str=base.deprecated_default)
deprecated_create = policy.DeprecatedRule(
    name='cyborg:device_profile:create',
    check_str=base.deprecated_is_admin)
deprecated_delete = policy.DeprecatedRule(
    name='cyborg:device_profile:delete',
    check_str=base.deprecated_default)

# new device_profile policies
device_profile_policies = [
    policy.DocumentedRuleDefault(
        name='cyborg:device_profile:get_all',
        check_str=base.PROJECT_READER_OR_SYSTEM_READER,
        description='Retrieve all device_profiles',
        operations=[
            {
                'path': '/v2/device_profiles',
                'method': 'GET'
            }],
        scope_types=['system', 'project'],
        deprecated_rule=deprecated_get_all,
        deprecated_reason=('request admin_or_owmer rule is too strict for '
                           'listing device_profile'),
        deprecated_since=versionutils.deprecated.WALLABY),
    policy.DocumentedRuleDefault(
        name='cyborg:device_profile:get_one',
        check_str=base.PROJECT_READER_OR_SYSTEM_READER,
        description='Retrieve a specific device_profile',
        operations=[
            {
                'path': '/v2/device_profiles/{device_profiles_uuid}',
                'method': 'GET'
            }],
        scope_types=['system', 'project'],
        deprecated_rule=deprecated_get_one,
        deprecated_reason=('request admin_or_owmer rule is too strict for '
                           'retrieving a device_profile'),
        deprecated_since=versionutils.deprecated.WALLABY),
    policy.DocumentedRuleDefault(
        name='cyborg:device_profile:create',
        check_str=base.SYSTEM_ADMIN,
        description='Create a device_profile',
        operations=[
            {
                'path': '/v2/device_profiles',
                'method': 'POST'
            }],
        scope_types=['system'],
        deprecated_rule=deprecated_create,
        deprecated_reason=('project_admin_or_owner is too permissive, '
                           'introduce system_scoped admin for creation'),
        deprecated_since=versionutils.deprecated.WALLABY),
    policy.DocumentedRuleDefault(
        name='cyborg:device_profile:delete',
        check_str=base.SYSTEM_ADMIN,
        description='Delete device_profile(s)',
        operations=[
            {
                'path': '/v2/device_profiles/{device_profiles_uuid}',
                'method': 'DELETE'},
            {
                'path': '/v2/device_profiles?value={device_profile_name1}',
                'method': 'DELETE'},
            ],
        scope_types=['system'],
        deprecated_rule=deprecated_delete,
        deprecated_reason=('project_admin_or_owner is too permissive, '
                           'introduce system_scoped admin for deletion'),
        deprecated_since=versionutils.deprecated.WALLABY),
]


def list_policies():
    return device_profile_policies
