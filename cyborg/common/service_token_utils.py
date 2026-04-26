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

"""Utilities for service token validation."""

from oslo_config import cfg


CONF = cfg.CONF


def is_service_request(ctxt):
    """Check if a request is coming from a service.

    A request is considered to come from a service if it has a
    service token and the service user has one of the roles
    configured in ``[keystone_authtoken] service_token_roles``
    (defaults to ``service``).

    :param ctxt: The request context.
    :returns: True if the request has a valid service token.
    """
    roles = ctxt.service_roles
    service_roles = set(CONF.keystone_authtoken.service_token_roles)
    return bool(roles and service_roles.intersection(roles))
