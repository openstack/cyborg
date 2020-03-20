# Copyright 2020 Intel Inc.
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
import wsme
from wsme import types as wtypes

from oslo_serialization import jsonutils

from cyborg.api.controllers import base
from cyborg.api.controllers import link
from cyborg.api.controllers import types
from cyborg.api import expose
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

    parent_id = types.integer
    """The parent ID of the deployable"""

    root_id = types.integer
    """The root ID of the deployable"""

    name = wtypes.text
    """The name of the deployable"""

    num_accelerators = types.integer
    """The number of accelerators of the deployable"""

    device_id = types.integer
    """The device on which the deployable is located"""

    attributes_list = wtypes.text
    """The json list of attributes of the deployable"""

    rp_uuid = types.uuid
    """The uuid of resouce provider which represents this deployable"""

    driver_name = wtypes.text
    """The driver name of this deployables"""

    bitstream_id = wtypes.text
    """The id of bitstream which has been program in this deployable"""

    links = wsme.wsattr([link.Link], readonly=True)
    """A list containing a self link"""

    def __init__(self, **kwargs):
        super(Deployable, self).__init__(**kwargs)
        self.fields = []
        for field in objects.Deployable.fields:
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    def convert_with_link(self, obj_dep):
        api_dep = Deployable(**obj_dep.as_dict())
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
        api_dep.attributes_list = jsonutils.dumps(attributes_list)
        return api_dep


class DeployableCollection(Deployable):
    """API representation of a collection of deployables."""

    deployables = [Deployable]
    """A list containing deployable objects"""

    def convert_with_links(self, obj_deps):
        collection = DeployableCollection()
        collection.deployables = [
            self.convert_with_link(obj_dep) for obj_dep in obj_deps]
        return collection


class DeployablesController(base.CyborgController,
                            DeployableCollection):
    """REST controller for Deployables."""

    @policy.authorize_wsgi("cyborg:deployable", "get_one")
    @expose.expose(Deployable, types.uuid)
    def get_one(self, uuid):
        """Retrieve information about the given deployable.

        :param uuid: UUID of a deployable.
        """
        obj_dep = objects.Deployable.get(pecan.request.context, uuid)
        return self.convert_with_link(obj_dep)

    @policy.authorize_wsgi("cyborg:deployable", "get_all")
    @expose.expose(DeployableCollection, wtypes.ArrayType(types.FilterType))
    def get_all(self, filters=None):
        """Retrieve a list of deployables.
        :param filters: a filter of FilterType to get deployables list by
        filter.
        """
        filters_dict = {}
        if filters:
            for filter in filters:
                filters_dict.update(filter.as_dict())
        context = pecan.request.context
        obj_deps = objects.Deployable.list(context, filters=filters_dict)
        return self.convert_with_links(obj_deps)
