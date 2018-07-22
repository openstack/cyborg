# Copyright 2018 Huawei Technologies Co.,LTD.
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

import json
import pecan
from six.moves import http_client
import wsme
from wsme import types as wtypes

from cyborg.api.controllers import base
from cyborg.api.controllers import link
from cyborg.api.controllers.v1 import types
from cyborg.api.controllers.v1 import utils as api_utils
from cyborg.api import expose
from cyborg.common import exception
from cyborg.common import policy
from cyborg import objects


class Deployable(base.APIBase):
    """API representation of a deployable.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of
    a deployable.
    """

    uuid = types.uuid
    """The UUID of the deployable"""

    name = wtypes.text
    """The name of the deployable"""

    parent_uuid = types.uuid
    """The parent UUID of the deployable"""

    root_uuid = types.uuid
    """The root UUID of the deployable"""

    address = wtypes.text
    """The address(pci/mdev) of the deployable"""

    host = wtypes.text
    """The host on which the deployable is located"""

    board = wtypes.text
    """The board of the deployable"""

    vendor = wtypes.text
    """The vendor of the deployable"""

    version = wtypes.text
    """The version of the deployable"""

    type = wtypes.text
    """The type of the deployable"""

    interface_type = wtypes.text
    """The interface type of deployable"""

    assignable = types.boolean
    """Whether the deployable is assignable"""

    instance_uuid = types.uuid
    """The UUID of the instance which deployable is assigned to"""

    availability = wtypes.text
    """The availability of the deployable"""

    attributes_list = wtypes.text
    """The json list of attributes of the deployable"""

    links = wsme.wsattr([link.Link], readonly=True)
    """A list containing a self link"""

    def __init__(self, **kwargs):
        super(Deployable, self).__init__(**kwargs)
        self.fields = []
        for field in objects.Deployable.fields:
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @classmethod
    def convert_with_links(cls, obj_dep):
        api_dep = cls(**obj_dep.as_dict())
        url = pecan.request.public_url
        api_dep.links = [
            link.Link.make_link('self', url, 'deployables', api_dep.uuid),
            link.Link.make_link('bookmark', url, 'deployables', api_dep.uuid,
                                bookmark=True)
            ]
        query = {"deployable_id": obj_dep.id}
        attr_get_list = objects.Attribute.get_by_filter(pecan.request.context,
                                                        query)
        attributes_list = []
        for exist_attr in attr_get_list:
            attributes_list.append({exist_attr.key: exist_attr.value})
        api_dep.attributes_list = json.dumps(attributes_list)
        return api_dep


class DeployableCollection(base.APIBase):
    """API representation of a collection of deployables."""

    deployables = [Deployable]
    """A list containing deployable objects"""

    @classmethod
    def convert_with_links(cls, obj_deps):
        collection = cls()
        collection.deployables = [Deployable.convert_with_links(obj_dep)
                                  for obj_dep in obj_deps]
        return collection


class DeployablePatchType(types.JsonPatchType):

    _api_base = Deployable

    @staticmethod
    def internal_attrs():
        defaults = types.JsonPatchType.internal_attrs()
        return defaults + ['/address', '/host', '/type']


class DeployablesController(base.CyborgController):
    """REST controller for Deployables."""

    _custom_actions = {'program': ['PATCH']}

    @policy.authorize_wsgi("cyborg:deployable", "program", False)
    @expose.expose(Deployable, types.uuid, body=[DeployablePatchType])
    def program(self, uuid, program_info):
        """Program a new deployable(FPGA).

        :param uuid: The uuid of the target deployable.
        :param program_info: JSON string containing what to program.
        """

        image_uuid = program_info[0]['value'][0]['image_uuid']
        obj_dep = objects.Deployable.get(pecan.request.context, uuid)
        # Set attribute of the new bitstream/image information
        obj_dep.add_attribute(pecan.request.context, 'image_uuid', image_uuid)
        # TODO (Li Liu) Trigger the program api in Agnet.
        return Deployable.convert_with_links(obj_dep)

    @policy.authorize_wsgi("cyborg:deployable", "create", False)
    @expose.expose(Deployable, body=types.jsontype,
                   status_code=http_client.CREATED)
    def post(self, dep):
        """Create a new deployable.

        :param dep: a deployable within the request body.
        """
        context = pecan.request.context
        obj_dep = objects.Deployable(context, **dep)
        new_dep = pecan.request.conductor_api.deployable_create(context,
                                                                obj_dep)
        # Set the HTTP Location Header
        pecan.response.location = link.build_url('deployables', new_dep.uuid)
        return Deployable.convert_with_links(new_dep)

    @policy.authorize_wsgi("cyborg:deployable", "get_one")
    @expose.expose(Deployable, types.uuid)
    def get_one(self, uuid):
        """Retrieve information about the given deployable.

        :param uuid: UUID of a deployable.
        """

        obj_dep = objects.Deployable.get(pecan.request.context, uuid)
        return Deployable.convert_with_links(obj_dep)

    @policy.authorize_wsgi("cyborg:deployable", "get_all")
    @expose.expose(DeployableCollection, int, types.uuid, wtypes.text,
                   wtypes.text, wtypes.ArrayType(types.FilterType))
    # TODO(wangzhh): Remove limit, marker, sort_key, sort_dir in next release.
    # They are used to compatible with R release client.
    def get_all(self, limit=None, marker=None, sort_key='id', sort_dir='asc',
                filters=None):
        """Retrieve a list of deployables."""
        filters_dict = {}
        self._generate_filters(limit, sort_key, sort_dir, filters_dict)
        if filters:
            for filter in filters:
                filters_dict.update(filter.as_dict())
        context = pecan.request.context
        if marker:
            marker_obj = objects.Deployable.get(context, marker)
            filters_dict["marker_obj"] = marker_obj
        obj_deps = objects.Deployable.list(context, filters=filters_dict)
        return DeployableCollection.convert_with_links(obj_deps)

    def _generate_filters(self, limit, sort_key, sort_dir, filters_dict):
        """This method are used to compatible with R release client."""
        if limit:
            filters_dict["limit"] = limit
        if sort_key:
            filters_dict["sort_key"] = sort_key
        if sort_dir:
            filters_dict["sort_dir"] = sort_dir

    @policy.authorize_wsgi("cyborg:deployable", "update")
    @expose.expose(Deployable, types.uuid, body=[DeployablePatchType])
    def patch(self, uuid, patch):
        """Update a deployable.

        Usage: curl -X PATCH {ip}:{port}/v1/accelerators/deployables/
        {deployable_uuid} -d '[{"path":"/instance_uuid","value":
        {instance_uuid}, "op":"replace"}]'  -H "Content-type:
        application/json"

        :param uuid: UUID of a deployable.
        :param patch: a json PATCH document to apply to this deployable.
        """
        context = pecan.request.context
        obj_dep = objects.Deployable.get(context, uuid)
        try:
            api_dep = Deployable(
                **api_utils.apply_jsonpatch(obj_dep.as_dict(), patch))
        except api_utils.JSONPATCH_EXCEPTIONS as e:
            raise exception.PatchError(patch=patch, reason=e)

        # Update only the fields that have changed
        for field in objects.Deployable.fields:
            try:
                patch_val = getattr(api_dep, field)
            except AttributeError:
                # Ignore fields that aren't exposed in the API
                continue
            if patch_val == wtypes.Unset:
                patch_val = None
            if obj_dep[field] != patch_val:
                obj_dep[field] = patch_val

        new_dep = pecan.request.conductor_api.deployable_update(context,
                                                                obj_dep)
        return Deployable.convert_with_links(new_dep)

    @policy.authorize_wsgi("cyborg:deployable", "delete")
    @expose.expose(None, types.uuid, status_code=http_client.NO_CONTENT)
    def delete(self, uuid):
        """Delete a deployable.

        :param uuid: UUID of a deployable.
        """
        context = pecan.request.context
        obj_dep = objects.Deployable.get(context, uuid)
        pecan.request.conductor_api.deployable_delete(context, obj_dep)
