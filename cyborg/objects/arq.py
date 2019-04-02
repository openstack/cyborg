# Copyright 2019 Beijing Lenovo Software Ltd.
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

from oslo_log import log as logging
from oslo_versionedobjects import base as object_base

from cyborg.db import api as dbapi
from cyborg import objects
from cyborg.objects import base
from cyborg.objects import fields as object_fields


LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class ARQ(base.CyborgObject, object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = dbapi.get_instance()
    fields = {
        'id': object_fields.IntegerField(nullable=False),
        'uuid': object_fields.UUIDField(nullable=False),
        'state': object_fields.ARQStateField(nullable=False),
        'device_profile': object_fields.ObjectField('DeviceProfile',
                                                    nullable=True),
        'hostname': object_fields.StringField(nullable=True),
        'device_rp_uuid': object_fields.UUIDField(nullable=True),
        'device_instance_uuid': object_fields.UUIDField(nullable=True),
        'attach_handle': object_fields.ObjectField('AttachHandle',
                                                   nullable=True),
    }

    @staticmethod
    def _from_db_object(arq, db_extarq):
        """Converts an ARQ to a formal object.

        :param arq: An object of the class ARQ
        :param db_extarq: A DB model of the object
        :return: The object of the class with the database entity added
        """
        device_profile_id = db_extarq.pop('device_profile_id', None)
        attach_handle_id = db_extarq.pop('attach_handle_id', None)

        for field in arq.fields:
            # if field == 'device_profile':
            #     arq._load_device_profile(device_profile_id)
            # if field == 'attach_handle':
            #     arq._load_device_profile(attach_handle_id)
            arq[field] = db_extarq[field]

        arq.obj_reset_changes()
        return arq

    def _load_device_profile(self, device_profile_id):
        self.device_profile = objects.DeviceProfile.\
            get_by_id(self._context, device_profile_id)

    def _load_attach_handle(self, attach_handle_id):
        self.attach_handle = objects.AttachHandle.\
            get_by_id(self._context, attach_handle_id)
