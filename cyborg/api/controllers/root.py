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

import pecan
from pecan import rest
from wsme import types as wtypes

from cyborg.api.controllers import base
from cyborg.api.controllers import v1
from cyborg.api import expose


VERSION1 = 'v1'


class Root(base.APIBase):
    name = wtypes.text
    """The name of the API"""

    description = wtypes.text
    """Some information about this API"""

    @staticmethod
    def convert():
        root = Root()
        root.name = 'OpenStack Cyborg API'
        root.description = (
            'Cyborg (previously known as Nomad) is an '
            'OpenStack project that aims to provide a general '
            'purpose management framework for acceleration '
            'resources (i.e. various types of accelerators '
            'such as Crypto cards, GPU, FPGA, NVMe/NOF SSDs, '
            'ODP, DPDK/SPDK and so on).')
        return root


class RootController(rest.RestController):
    _versions = [VERSION1]
    """All supported API versions"""

    _default_version = VERSION1
    """The default API version"""

    v1 = v1.Controller()

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
