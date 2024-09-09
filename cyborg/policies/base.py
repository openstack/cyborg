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

# All legacy policy and new policy mapping for all V2 APIs can be found
# here:https://wiki.openstack.org/wiki/Cyborg/Policy

DEPRECATED_REASON = """
Cyborg API policies are introducing new default roles with scope_type
capabilities. We will start to deprecate old policies from WALLABY release,
and are going to ignore all the old policies silently from X release.
Be sure to take these new defaults into consideration if you are
relying on overrides in your deployment for the policy API.
"""

deprecated_default = 'rule:admin_or_owner'
deprecated_is_admin = 'rule:is_admin'

ADMIN_OR_OWNER = 'rule:admin_or_owner'

DEPRECATED_ADMIN_OR_OWNER = policy.DeprecatedRule(
    name=ADMIN_OR_OWNER,
    check_str='is_admin:True or project_id:%(project_id)s',
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)

deprecated_default_policies = [
    # is_public_api is set in the environment from AuthTokenMiddleware
    policy.RuleDefault(
        name='public_api',
        check_str='is_public_api:True',
        description='legacy rule of Internal flag for public API routes',
        deprecated_for_removal=True,
        deprecated_reason=DEPRECATED_REASON,
        deprecated_since=versionutils.deprecated.WALLABY),
    # The policy check "@" will always accept an access. The empty list
    # (``[]``) or the empty string (``""``) is equivalent to the "@"
    policy.RuleDefault(
        name='allow',
        check_str='@',
        description='legacy rule: any access will be passed',
        deprecated_for_removal=True,
        deprecated_reason=DEPRECATED_REASON,
        deprecated_since=versionutils.deprecated.WALLABY),
    # the policy check "!" will always reject an access.
    policy.RuleDefault(
        name='deny',
        check_str='!',
        description='legacy rule: all access will be forbidden',
        deprecated_for_removal=True,
        deprecated_reason=DEPRECATED_REASON,
        deprecated_since=versionutils.deprecated.WALLABY),
    policy.RuleDefault(
        name='default',
        check_str='rule:admin_or_owner',
        description='Legacy rule for default rule',
        deprecated_for_removal=True,
        deprecated_reason=DEPRECATED_REASON,
        deprecated_since=versionutils.deprecated.WALLABY),
    policy.RuleDefault(
        name='is_admin',
        check_str='rule:admin_api',
        description='Full read/write API access',
        deprecated_for_removal=True,
        deprecated_reason=DEPRECATED_REASON,
        deprecated_since=versionutils.deprecated.WALLABY),
    policy.RuleDefault(
        name='admin_or_owner',
        check_str='is_admin:True or project_id:%(project_id)s',
        description='Admin or owner API access',
        deprecated_for_removal=True,
        deprecated_reason=DEPRECATED_REASON,
        deprecated_since=versionutils.deprecated.WALLABY),
    policy.RuleDefault(
        name='admin_or_user',
        check_str='is_admin:True or user_id:%(user_id)s',
        description='Admin or user API access',
        deprecated_for_removal=True,
        deprecated_reason=DEPRECATED_REASON,
        deprecated_since=versionutils.deprecated.WALLABY),
]

ADMIN = 'rule:admin_api'
PROJECT_ADMIN = 'rule:project_admin_api'
PROJECT_MEMBER = 'rule:project_member_api'
PROJECT_READER = 'rule:project_reader_api'
PROJECT_MEMBER_OR_ADMIN = 'rule:project_member_or_admin'
PROJECT_READER_OR_ADMIN = 'rule:project_reader_or_admin'

# NOTE(yumeng): Keystone already support implied roles means assignment
# of one role implies the assignment of another. New defaults roles
# `reader`, `member` also has been added in bootstrap. If the bootstrap
# process is re-run, and a `reader`, `member`, or `admin` role already
# exists, a role implication chain will be created: `admin` implies
# `member` implies `reader`.
# For example: If we give access to 'reader' it means the 'admin' and
# 'member' also get access.

# NOTE(yumeng) the rules listed include both old rules and new rules.
# legacy rules list: 'public_api','allow','deny','admin_api','is_admin',
# 'admin_or_owner','admin_or_user'.
# new rules list: project_admin_api, project_member_api, project_reader_api,
# project_member_or_admin, project_reader_or_admin .
default_policies = [
    policy.RuleDefault(
        name='admin_api',
        check_str='role:admin or role:administrator',
        description='Legacy rule for cloud admin access'),
    policy.RuleDefault(
        name="project_admin_api",
        check_str="role:admin and project_id:%(project_id)s",
        description="Default rule for Project level admin APIs."),
    policy.RuleDefault(
        name="project_member_api",
        check_str="role:member and project_id:%(project_id)s",
        description="Default rule for Project level non admin APIs."),
    policy.RuleDefault(
        name="project_reader_api",
        check_str="role:reader and project_id:%(project_id)s",
        description="Default rule for Project level read only APIs."),
    policy.RuleDefault(
        "project_member_or_admin",
        "rule:project_member_api or rule:admin_api",
        "Default rule for Project Member or admin APIs.",
        deprecated_rule=DEPRECATED_ADMIN_OR_OWNER),
    policy.RuleDefault(
        "project_reader_or_admin",
        "rule:project_reader_api or rule:admin_api",
        "Default rule for Project reader or admin APIs.",
        deprecated_rule=DEPRECATED_ADMIN_OR_OWNER)
]


def list_policies():
    return default_policies \
        + deprecated_default_policies
