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

    def report_data(self, context, hostname, driver_device_list):
        """Signal to conductor service to update the cyborg DB
        :parma context: request context.
        """
        cctxt = self.client.prepare(topic=self.topic)
        cctxt.call(context, 'report_data', hostname=hostname,
                   driver_device_list=driver_device_list)

    def device_profile_create(self, context, obj_devprof):
        """Signal to conductor service to create a device_profile.

        :param context: request context.
        :param obj_devprof: a created (but not saved) device_profile object.
        :returns: created device_profile object.
        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'device_profile_create',
                          obj_devprof=obj_devprof)

    def device_profile_delete(self, context, obj_devprof):
        """Signal to conductor service to delete a device_profile.
        :param context: request context.
        :param obj_devprof: a device_profile object to delete.
        """
        cctxt = self.client.prepare(topic=self.topic)
        cctxt.call(context, 'device_profile_delete',
                   obj_devprof=obj_devprof)

    def arq_create(self, context, obj_extarq, devprof_id):
        """Signal to conductor service to create an accelerator requests.

        :param context: request context.
        :param obj_extarq: a created (but not saved) accelerator_requests
        object
        :param devprof_id: a device profile id
        :returns: saved accelerator_requests object.
        """
        cctxt = self.client.prepare(topic=self.topic)
        return cctxt.call(context, 'arq_create', obj_extarq=obj_extarq,
                          devprof_id=devprof_id)

    def arq_delete_by_uuid(self, context, arqs):
        """Signal to conductor service to delete accelerator requests by
        ARQ UUIDs.

        :param context: request context.
        :param arqs: ARQ UUIDs joined with ','
        """
        cctxt = self.client.prepare(topic=self.topic)
        cctxt.call(context, 'arq_delete_by_uuid', arqs=arqs)

    def arq_delete_by_instance_uuid(self, context, instance):
        """Signal to conductor service to delete accelerator requests by
        instance UUID.

        :param context: request context.
        :param instance: UUID of instance whose ARQs need to be deleted
        """
        cctxt = self.client.prepare(topic=self.topic)
        cctxt.call(context, 'arq_delete_by_instance_uuid', instance=instance)
