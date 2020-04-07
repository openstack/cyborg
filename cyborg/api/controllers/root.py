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

import importlib
import pecan
from pecan import rest
from wsme import types as wtypes

from cyborg.api.controllers import base
from cyborg.api.controllers import link
from cyborg.api.controllers import v2
from cyborg.api import expose


class APIStatus(object):
    CURRENT = "CURRENT"
    SUPPORTED = "SUPPORTED"
    DEPRECATED = "DEPRECATED"
    EXPERIMENTAL = "EXPERIMENTAL"


class Version(base.APIBase):
    """An API version representation."""

    id = wtypes.text
    """The ID of the version, also acts as the release number"""

    status = wtypes.text
    """The state of this API version"""

    max_version = wtypes.text
    """The maximum version supported"""

    min_version = wtypes.text
    """The minimum version supported"""

    links = [link.Link]
    """A Link that points to a specific version of the API"""

    @staticmethod
    def convert(id, status=APIStatus.CURRENT):
        version = Version()
        if id == "v1":
            version.max_version = None
            version.min_version = None
        else:
            v = importlib.import_module(
                'cyborg.api.controllers.%s.versions' % id)
            version.max_version = v.max_version_string()
            version.min_version = v.min_version_string()
        version.id = id
        version.status = status
        version.links = [link.Link.make_link('self', pecan.request.host_url,
                                             id, '', bookmark=True)]
        return version


class Root(base.APIBase):
    name = wtypes.text
    """The name of the API"""

    description = wtypes.text
    """Some information about this API"""

    versions = [Version]
    """Links to all the versions available in this API"""

    default_version = Version
    """A link to the default version of the API"""

    @staticmethod
    def convert():
        root = Root()
        root.name = 'OpenStack Cyborg API'
        root.description = (
            "Cyborg is the OpenStack project for lifecycle "
            "management of hardware accelerators, such as GPUs,"
            "FPGAs, AI chips, security accelerators, etc.")
        root.versions = [Version.convert('v2')]
        root.default_version = Version.convert('v2')
        return root


class RootController(rest.RestController):
    _versions = [base.API_V2]
    """All supported API versions"""

    _default_version = base.API_V2
    """The default API version"""

    v2 = v2.Controller()

    @expose.expose(Root)
    def get(self):
        return Root.convert()

    @pecan.expose()
    def _route(self, args, request=None):
        """Overrides the default routing behavior.

        It redirects the request to the default version of the cyborg API
        if the version number is not specified in the url.
        """

        if args[0] and args[0] not in self._versions:
            args = [self._default_version] + args
        return super(RootController, self)._route(args)
