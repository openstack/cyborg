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

from oslo_config import cfg
from oslo_middleware import cors

from cyborg import version
from cyborg.common import rpc


def set_lib_defaults():
    rpc.set_defaults(control_exchange='cyborg')
    cfg.CONF.set_default(
        'service_token_roles_required', True, group='keystone_authtoken'
    )
    cors.set_defaults(
        allow_headers=[
            'X-Auth-Token',
            'X-Openstack-Request-Id',
            'X-Identity-Status',
            'X-Roles',
            'X-Service-Catalog',
            'X-User-Id',
            'X-Tenant-Id',
            'OpenStack-API-Version',
        ],
        expose_headers=[
            'X-Auth-Token',
            'X-Openstack-Request-Id',
            'X-Subject-Token',
            'X-Service-Token',
            'OpenStack-API-Version',
        ],
        allow_methods=['GET', 'PUT', 'POST', 'DELETE', 'PATCH'],
    )


def parse_args(argv, default_config_files=None):
    set_lib_defaults()

    version_string = version.version_info.release_string()
    cfg.CONF(
        argv[1:],
        project='cyborg',
        version=version_string,
        default_config_files=default_config_files,
    )
    rpc.init(cfg.CONF)
