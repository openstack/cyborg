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
from oslo_context import context
from pecan import hooks

from cyborg.common import policy
from cyborg.conductor import rpcapi


class ConfigHook(hooks.PecanHook):
    """Attach the config object to the request so controllers can get to it."""

    def before(self, state):
        state.request.cfg = cfg.CONF


class PublicUrlHook(hooks.PecanHook):
    """Attach the right public_url to the request.

    Attach the right public_url to the request so resources can create
    links even when the API service is behind a proxy or SSL terminator.
    """

    def before(self, state):
        state.request.public_url = (
            cfg.CONF.api.public_endpoint or state.request.host_url)


class ConductorAPIHook(hooks.PecanHook):
    """Attach the conductor_api object to the request."""

    def __init__(self):
        self.conductor_api = rpcapi.ConductorAPI()

    def before(self, state):
        state.request.conductor_api = self.conductor_api


class ContextHook(hooks.PecanHook):
    """Configures a request context and attaches it to the request.

    The following HTTP request headers are used:

    X-User-Id or X-User:
        Used for context.user.

    X-Tenant-Id or X-Tenant:
        Used for context.tenant.

    X-Auth-Token:
        Used for context.auth_token.

    X-Roles:
        Used for setting context.is_admin flag to either True or False.
        The flag is set to True, if X-Roles contains either an administrator
        or admin substring. Otherwise it is set to False.

    """

    def __init__(self, public_api_routes):
        self.public_api_routes = public_api_routes
        super(ContextHook, self).__init__()

    def before(self, state):
        headers = state.request.headers

        creds = {
            'user_name': headers.get('X-User-Name'),
            'user': headers.get('X-User-Id'),
            'project_name': headers.get('X-Project-Name'),
            'tenant': headers.get('X-Project-Id'),
            'domain': headers.get('X-User-Domain-Id'),
            'domain_name': headers.get('X-User-Domain-Name'),
            'auth_token': headers.get('X-Auth-Token'),
            'roles': headers.get('X-Roles', '').split(','),
        }

        is_admin = policy.authorize('is_admin', creds, creds)
        state.request.context = context.RequestContext(
            is_admin=is_admin, **creds)
