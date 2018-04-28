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

"""Client side of the conductor RPC API."""

from oslo_config import cfg
import oslo_messaging as messaging

from cyborg.common import constants
from cyborg.common import rpc
from cyborg.objects import base as objects_base


CONF = cfg.CONF


class ConductorAPI(object):
    """Client side of the conductor RPC API.

    API version history:

    |    1.0 - Initial version.

    """

    RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        super(ConductorAPI, self).__init__()
        self.topic = topic or constants.CONDUCTOR_TOPIC
        target = messaging.Target(topic=self.topic,
                                  version='1.0')
        serializer = objects_base.CyborgObjectSerializer()
        self.client = rpc.get_client(target,
                                     version_cap=self.RPC_API_VERSION,
                                     serializer=serializer)

    def accelerator_create(self, context, obj_acc):
        """Signal to conductor service to create an accelerator.

        :param context: request context.
        :param obj_acc: a created (but not saved) accelerator object.
        :returns: created accelerator object.
        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'accelerator_create', obj_acc=obj_acc)

    def accelerator_update(self, context, obj_acc):
        """Signal to conductor service to update an accelerator.

        :param context: request context.
        :param obj_acc: an accelerator object to update.
        :returns: updated accelerator object.
        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'accelerator_update', obj_acc=obj_acc)

    def accelerator_delete(self, context, obj_acc):
        """Signal to conductor service to delete an accelerator.

        :param context: request context.
        :param obj_acc: an accelerator object to delete.
        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'accelerator_delete', obj_acc=obj_acc)

    def accelerator_list_one(self, context, obj_acc):
        """Signal to conductor service to list an accelerator.

        :param context: request context.
        :param obj_acc: an accelerator object to list.
        :returns: accelerator object.
        """
        cctxt = self.client.prepare(topic=self.topic)
        cctxt.call(context, 'get_one', obj_acc=obj_acc)

    def accelerator_list_all(self, context, obj_acc):
        """Signal to conductor service to list all accelerators.

        :param context: request context.
        :param obj_acc: accelerator objects to list.
        :returns: accelerator objects.

        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'get_all', obj_acc=obj_acc)

    def deployable_create(self, context, obj_dep):
        """Signal to conductor service to create a deployable.

        :param context: request context.
        :param obj_dep: a created (but not saved) deployable object.
        :returns: created deployable object.
        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'deployable_create', obj_dep=obj_dep)

    def deployable_update(self, context, obj_dep):
        """Signal to conductor service to update a deployable.

        :param context: request context.
        :param obj_dep: a deployable object to update.
        :returns: updated deployable object.
        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'deployable_update', obj_dep=obj_dep)

    def deployable_delete(self, context, obj_dep):
        """Signal to conductor service to delete a deployable.

        :param context: request context.
        :param obj_dep: a deployable object to delete.
        """
        cctxt = self.client.prepare(topic=self.topic)
        cctxt.call(context, 'deployable_delete', obj_dep=obj_dep)

    def deployable_get(self, context, uuid):
        """Signal to conductor service to get a deployable.

        :param context: request context.
        :param uuid: UUID of a deployable.
        :returns: requested deployable object.
        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'deployable_get', uuid=uuid)

    def deployable_get_by_host(self, context, host):
        """Signal to conductor service to get a deployable by host.

        :param context: request context.
        :param host: host on which the deployable is located.
        :returns: requested deployable object.
        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'deployable_get_by_host', host=host)

    def deployable_list(self, context):
        """Signal to conductor service to get a list of deployables.

        :param context: request context.
        :returns: a list of deployable objects.
        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'deployable_list')
