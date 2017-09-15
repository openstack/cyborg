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
from six.moves import http_client
import wsme
from wsme import types as wtypes

from cyborg.api.controllers import base
from cyborg.api.controllers import link
from cyborg.api.controllers.v1 import types
from cyborg.api import expose
from cyborg.common import policy
from cyborg import objects


class Accelerator(base.APIBase):
    """API representation of a accelerator.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of
    a accelerator.
    """

    uuid = types.uuid
    name = wtypes.text
    description = wtypes.text
    project_id = types.uuid
    user_id = types.uuid
    device_type = wtypes.text
    acc_type = wtypes.text
    acc_capability = wtypes.text
    vendor_id = wtypes.text
    product_id = wtypes.text
    remotable = wtypes.IntegerType()

    links = wsme.wsattr([link.Link], readonly=True)
    """A list containing a self link"""

    def __init__(self, **kwargs):
        self.fields = []
        for field in objects.Accelerator.fields:
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @classmethod
    def convert_with_links(cls, rpc_acc):
        accelerator = Accelerator(**rpc_acc.as_dict())
        url = pecan.request.public_url
        accelerator.links = [
            link.Link.make_link('self', url, 'accelerators',
                                accelerator.uuid),
            link.Link.make_link('bookmark', url, 'accelerators',
                                accelerator.uuid, bookmark=True)
            ]

        return accelerator


class AcceleratorsControllerBase(rest.RestController):
    def _get_resource(self, uuid):
        self._resource = objects.Accelerator.get(pecan.request.context, uuid)
        return self._resource


class AcceleratorsController(AcceleratorsControllerBase):
    """REST controller for Accelerators."""

    @policy.authorize_wsgi("cyborg:accelerator", "create", False)
    @expose.expose(Accelerator, body=types.jsontype,
                   status_code=http_client.CREATED)
    def post(self, accelerator):
        """Create a new accelerator.

        :param accelerator: an accelerator within the request body.
        """
        context = pecan.request.context
        rpc_acc = objects.Accelerator(context, **accelerator)
        new_acc = pecan.request.conductor_api.accelerator_create(
            context, rpc_acc)
        # Set the HTTP Location Header
        pecan.response.location = link.build_url('accelerators',
                                                 new_acc.uuid)
        return Accelerator.convert_with_links(new_acc)
