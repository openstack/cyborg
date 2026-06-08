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


deprecated_get_one = policy.DeprecatedRule(
    name='cyborg:attribute:get_one',
    check_str='rule:admin_api',
    deprecated_reason=(
        'rule:admin_api is replaced by project_manager_or_admin '
        'to grant the manager persona read access to accelerator '
        'capability metadata for capacity planning and '
        'troubleshooting'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)
deprecated_get_all = policy.DeprecatedRule(
    name='cyborg:attribute:get_all',
    check_str='rule:admin_api',
    deprecated_reason=(
        'rule:admin_api is replaced by project_manager_or_admin '
        'to grant the manager persona read access to accelerator '
        'capability metadata for capacity planning and '
        'troubleshooting'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)
deprecated_create = policy.DeprecatedRule(
    name='cyborg:attribute:create',
    check_str='rule:admin_api',
    deprecated_reason=(
        'rule:admin_api is retained as the default for attribute '
        'create as attributes describe shared physical '
        'infrastructure properties populated by cyborg-agent'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)
deprecated_delete = policy.DeprecatedRule(
    name='cyborg:attribute:delete',
    check_str='rule:admin_api',
    deprecated_reason=(
        'rule:admin_api is retained as the default for attribute '
        'delete as attributes describe shared physical '
        'infrastructure properties populated by cyborg-agent'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)

attribute_policies = [
    policy.DocumentedRuleDefault(
        name='cyborg:attribute:get_all',
        check_str=base.PROJECT_MANAGER_OR_ADMIN,
        description='Retrieve all attribute records',
        operations=[
            {'path': '/v2/attributes', 'method': 'GET'},
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_get_all,
    ),
    policy.DocumentedRuleDefault(
        name='cyborg:attribute:get_one',
        check_str=base.PROJECT_MANAGER_OR_ADMIN,
        description='Show attribute detail',
        operations=[
            {'path': '/v2/attributes/{uuid}', 'method': 'GET'},
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_get_one,
    ),
    policy.DocumentedRuleDefault(
        name='cyborg:attribute:create',
        check_str=base.ADMIN,
        description='Create an attribute record',
        operations=[
            {'path': '/v2/attributes', 'method': 'POST'},
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_create,
    ),
    policy.DocumentedRuleDefault(
        name='cyborg:attribute:delete',
        check_str=base.ADMIN,
        description='Delete an attribute record',
        operations=[
            {'path': '/v2/attributes/{uuid}', 'method': 'DELETE'},
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_delete,
    ),
]


def list_policies():
    return attribute_policies
