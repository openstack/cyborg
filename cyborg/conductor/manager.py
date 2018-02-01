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

import oslo_messaging as messaging

from cyborg.conf import CONF
from cyborg import objects


class ConductorManager(object):
    """Cyborg Conductor manager main class."""

    RPC_API_VERSION = '1.0'
    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, topic, host=None):
        super(ConductorManager, self).__init__()
        self.topic = topic
        self.host = host or CONF.host

    def periodic_tasks(self, context, raise_on_error=False):
        pass

    def accelerator_create(self, context, obj_acc):
        """Create a new accelerator.

        :param context: request context.
        :param obj_acc: a changed (but not saved) accelerator object.
        :returns: created accelerator object.
        """
        base_options = {
            'project_id': context.tenant,
            'user_id': context.user
            }
        obj_acc.update(base_options)
        obj_acc.create(context)
        return obj_acc

    def accelerator_update(self, context, obj_acc):
        """Update an accelerator.

        :param context: request context.
        :param obj_acc: an accelerator object to update.
        :returns: updated accelerator object.
        """
        obj_acc.save(context)
        return obj_acc

    def accelerator_delete(self, context, obj_acc):
        """Delete an accelerator.

        :param context: request context.
        :param obj_acc: an accelerator object to delete.
        """
        obj_acc.destroy(context)

    def deployable_create(self, context, obj_dep):
        """Create a new deployable.

        :param context: request context.
        :param obj_dep: a changed (but not saved) obj_dep object.
        :returns: created obj_dep object.
        """
        obj_dep.create(context)
        return obj_dep

    def deployable_update(self, context, obj_dep):
        """Update a deployable.

        :param context: request context.
        :param obj_dep: a deployable object to update.
        :returns: updated deployable object.
        """
        obj_dep.save(context)
        return obj_dep

    def deployable_delete(self, context, obj_dep):
        """Delete a deployable.

        :param context: request context.
        :param obj_dep: a deployable object to delete.
        """
        obj_dep.destroy(context)

    def deployable_get(self, context, uuid):
        """Retrieve a deployable.

        :param context: request context.
        :param uuid: UUID of a deployable.
        :returns: requested deployable object.
        """
        return objects.Deployable.get(context, uuid)

    def deployable_get_by_host(self, context, host):
        """Retrieve a deployable.

        :param context: request context.
        :param host: host on which the deployable is located.
        :returns: requested deployable object.
        """
        return objects.Deployable.get_by_host(context, host)

    def deployable_list(self, context):
        """Retrieve a list of deployables.

        :param context: request context.
        :returns: a list of deployable objects.
        """
        return objects.Deployable.list(context)
