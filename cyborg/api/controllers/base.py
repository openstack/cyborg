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

import datetime
import functools
import inspect

import microversion_parse
import pecan
import wsme

from oslo_log import log as logging
from pecan import rest
from webob import exc
from wsme import types as wtypes


LOG = logging.getLogger(__name__)


API_V2 = 'v2'
SERVICE_TYPE = 'accelerator'


class APIBase(wtypes.Base):
    created_at = wsme.wsattr(datetime.datetime, readonly=True)
    """The time in UTC at which the object is created"""

    updated_at = wsme.wsattr(datetime.datetime, readonly=True)
    """The time in UTC at which the object is updated"""

    def as_dict(self):
        """Render this object as a dict of its fields."""
        return {
            k: getattr(self, k)
            for k in self.fields
            if hasattr(self, k) and getattr(self, k) != wsme.Unset
        }


class CyborgController(rest.RestController):
    def _handle_patch(self, method, remainder, request=None):
        """Routes ``PATCH`` _custom_actions."""
        # route to a patch_all or get if no additional parts are available
        if not remainder or remainder == ['']:
            controller = self._find_controller('patch_all', 'patch')
            if controller:
                return controller, []
            pecan.abort(404)

        controller = getattr(self, remainder[0], None)
        if controller and not inspect.ismethod(controller):
            return pecan.routing.lookup_controller(controller, remainder[1:])
        # route to custom_action
        match = self._handle_custom_action(method, remainder, request)
        if match:
            return match

        # finally, check for the regular patch_one/patch requests
        controller = self._find_controller('patch_one', 'patch')
        if controller:
            return controller, remainder

        pecan.abort(405)


@functools.total_ordering
class Version:
    """API Version object."""

    current_api_version = 'OpenStack-API-Version'
    """HTTP Header string carrying the requested version"""

    min_api_version = 'OpenStack-API-Minimum-Version'
    """HTTP response header"""

    max_api_version = 'OpenStack-API-Maximum-Version'
    """HTTP response header"""

    def __init__(self, headers, default_version, latest_version):
        """Create an API Version object from the supplied headers.

        :param headers: webob headers
        :param default_version: version to use if not specified in headers
        :param latest_version: version to use if latest is requested
        :raises: webob.HTTPNotAcceptable

        """
        (self.major, self.minor) = Version.parse_headers(
            headers, default_version, latest_version
        )

    def __repr__(self):
        return '%s.%s' % (self.major, self.minor)

    @staticmethod
    def parse_headers(headers, default_version, latest_version):
        """Determine the API version requested based on the headers supplied.

        Per the `OpenStack API-WG guideline`_ the ``OpenStack-API-Version``
        header carries the service type followed by the requested version,
        for example ``OpenStack-API-Version: accelerator 2.1``.
        ``microversion_parse`` handles this standard format.  A bare
        version string without the service type prefix is also accepted
        for backward compatibility with older clients but triggers a
        deprecation warning.

        .. _OpenStack API-WG guideline:
           https://specs.openstack.org/openstack/api-wg/guidelines/
           microversion_specification.html

        :param headers: webob headers
        :param default_version: version to use if not specified in headers
        :param latest_version: version to use if latest is requested
        :returns: a tuple of (major, minor) version numbers
        :raises: webob.HTTPNotAcceptable

        """
        minimal_version = (2, 0)
        service_type = SERVICE_TYPE

        # Try the standard format first:
        #   OpenStack-API-Version: accelerator <version>
        version_str = microversion_parse.get_version(
            headers, service_type=service_type
        )

        if version_str is None:
            # Fall back to a bare version string without the service
            # type prefix for backward compatibility.
            raw = headers.get(Version.current_api_version)
            if raw is not None:
                LOG.warning(
                    'Received OpenStack-API-Version header without '
                    'the service type prefix.  Clients should send '
                    "'OpenStack-API-Version: %s <version>' "
                    'per the API-WG guideline.',
                    service_type,
                )
                version_str = raw
            else:
                version_str = default_version

        if version_str is None:
            return minimal_version

        if version_str.lower() == 'latest':
            parse_str = latest_version
        else:
            parse_str = version_str

        try:
            version = microversion_parse.parse_version_string(parse_str)
        except TypeError:
            raise exc.HTTPNotAcceptable(
                "Invalid value for %s header" % Version.current_api_version
            )
        return (version.major, version.minor)

    def __gt__(self, other):
        return (self.major, self.minor) > (other.major, other.minor)

    def __eq__(self, other):
        return (self.major, self.minor) == (other.major, other.minor)

    def __ne__(self, other):
        return not self.__eq__(other)
