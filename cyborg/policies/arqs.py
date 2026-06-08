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


deprecated_get_all = policy.DeprecatedRule(
    name='cyborg:arq:get_all',
    check_str=base.deprecated_default,
    deprecated_reason=(
        'rule:default (admin_or_owner) is replaced by '
        'project_reader_or_admin to grant readers explicit '
        'read-only access to their own ARQs'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)
deprecated_get_one = policy.DeprecatedRule(
    name='cyborg:arq:get_one',
    check_str=base.deprecated_default,
    deprecated_reason=(
        'rule:default (admin_or_owner) is replaced by '
        'project_reader_or_admin to grant readers explicit '
        'read-only access to their own ARQs'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)
# ARQ create previously used project_member_or_admin rather than the
# admin_or_owner default used by the other ARQ operations.
deprecated_create = policy.DeprecatedRule(
    name='cyborg:arq:create',
    check_str='rule:project_member_or_admin',
    deprecated_reason=(
        'rule:project_member_or_admin is replaced by '
        'project_member_or_service to additionally accept the '
        'service role for machine-to-machine APIs'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)
deprecated_delete = policy.DeprecatedRule(
    name='cyborg:arq:delete',
    check_str=base.deprecated_default,
    deprecated_reason=(
        'rule:default (admin_or_owner) is replaced by '
        'project_member_or_service to use modern personas'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)
deprecated_update = policy.DeprecatedRule(
    name='cyborg:arq:update',
    check_str=base.deprecated_default,
    deprecated_reason=(
        'rule:default (admin_or_owner) is replaced by '
        'project_member_or_service to use modern personas'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)

arq_policies = [
    policy.DocumentedRuleDefault(
        name='cyborg:arq:get_all',
        check_str=base.PROJECT_READER_OR_ADMIN,
        description='Retrieve all accelerator requests',
        operations=[
            {'path': '/v2/accelerator_requests', 'method': 'GET'},
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_get_all,
    ),
    policy.DocumentedRuleDefault(
        name='cyborg:arq:get_one',
        check_str=base.PROJECT_READER_OR_ADMIN,
        description='Retrieve a specific accelerator request',
        operations=[
            {
                'path': '/v2/accelerator_requests/{arqs_uuid}',
                'method': 'GET',
            },
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_get_one,
    ),
    policy.DocumentedRuleDefault(
        name='cyborg:arq:create',
        check_str=base.PROJECT_MEMBER_OR_SERVICE,
        description='Create accelerator request records',
        operations=[
            {'path': '/v2/accelerator_requests', 'method': 'POST'},
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_create,
    ),
    policy.DocumentedRuleDefault(
        name='cyborg:arq:delete',
        check_str=base.PROJECT_MEMBER_OR_SERVICE,
        description='Delete accelerator request records',
        operations=[
            {'path': '/v2/accelerator_requests', 'method': 'DELETE'},
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_delete,
    ),
    policy.DocumentedRuleDefault(
        name='cyborg:arq:update',
        check_str=base.PROJECT_MEMBER_OR_SERVICE,
        description='Update accelerator request records',
        operations=[
            {'path': '/v2/accelerator_requests', 'method': 'PATCH'},
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_update,
    ),
]


def list_policies():
    return arq_policies
