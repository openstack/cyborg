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
    name='cyborg:deployable:get_one',
    check_str='rule:admin_api',
    deprecated_reason=(
        'rule:admin_api is replaced by project_manager_or_admin '
        'to grant the manager persona read access to deployable '
        'inventory for capacity planning and troubleshooting'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)
deprecated_get_all = policy.DeprecatedRule(
    name='cyborg:deployable:get_all',
    check_str='rule:admin_api',
    deprecated_reason=(
        'rule:admin_api is replaced by project_manager_or_admin '
        'to grant the manager persona read access to deployable '
        'inventory for capacity planning and troubleshooting'
    ),
    deprecated_since=versionutils.deprecated.GAZPACHO,
)
deployable_policies = [
    policy.DocumentedRuleDefault(
        name='cyborg:deployable:get_all',
        check_str=base.PROJECT_MANAGER_OR_ADMIN,
        description='Retrieve all deployable records',
        operations=[
            {'path': '/v2/deployables', 'method': 'GET'},
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_get_all,
    ),
    policy.DocumentedRuleDefault(
        name='cyborg:deployable:get_one',
        check_str=base.PROJECT_MANAGER_OR_ADMIN,
        description='Show deployable detail',
        operations=[
            {'path': '/v2/deployables/{uuid}', 'method': 'GET'},
        ],
        scope_types=['project'],
        deprecated_rule=deprecated_get_one,
    ),
    # No deprecated_rule: base.ADMIN == 'rule:admin_api' is unchanged.
    policy.DocumentedRuleDefault(
        name='cyborg:deployable:program',
        check_str=base.ADMIN,
        description='Program a deployable (FPGA bitstream reprogramming)',
        operations=[
            {
                'path': '/v2/deployables/{uuid}/program',
                'method': 'PATCH',
            },
        ],
        scope_types=['project'],
    ),
]


def list_policies():
    return deployable_policies
