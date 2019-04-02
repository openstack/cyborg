# -*- encoding: utf-8 -*-
# Copyright (c) 2019 ZTE Corporation
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
from cyborg.objects import base
from cyborg.objects import fields as object_fields


LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class DeviceProfile(base.CyborgObject, object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': object_fields.IntegerField(nullable=False),
        'uuid': object_fields.UUIDField(nullable=False),
        'name': object_fields.StringField(nullable=False),
        'profile_json': object_fields.StringField(nullable=False),
    }

    def create(self, context):
        """Create a device_profile record in the DB."""
        values = self.obj_get_changes()
        db_device_profile = self.dbapi.device_profile_create(context, values)
        self._from_db_object(self, db_device_profile)

    @classmethod
    def get(cls, context, uuid):
        """Find a DB Device_profile and return a Obj Device_profile."""
        db_device_profile = cls.dbapi.device_profile_get_by_uuid(context, uuid)
        obj_device_profile = cls._from_db_object(cls(context),
                                                 db_device_profile)
        return obj_device_profile

    @classmethod
    def list(cls, context, filters={}):
        """Return a list of Device_profile objects."""
        if filters:
            sort_dir = filters.pop('sort_dir', 'desc')
            sort_key = filters.pop('sort_key', 'created_at')
            limit = filters.pop('limit', None)
            marker = filters.pop('marker_obj', None)
            db_device_profiles = cls.dbapi.device_profile_list_by_filters(
                context, filters, sort_dir=sort_dir, sort_key=sort_key,
                limit=limit, marker=marker)
        else:
            db_device_profiles = cls.dbapi.device_profile_list(context)
        return cls._from_db_object_list(db_device_profiles, context)

    def save(self, context):
        """Update a Device_profile record in the DB."""
        updates = self.obj_get_changes()
        db_device_profile = self.dbapi.device_profile_update(context,
                                                             self.uuid,
                                                             updates)
        self._from_db_object(self, db_device_profile)

    def destroy(self, context):
        """Delete the Device_profile from the DB."""
        self.dbapi.device_profile_delete(context, self.uuid)
        self.obj_reset_changes()

    @classmethod
    def get_by_id(cls, context, id):
        """Find a device_profile and return an Obj DeviceProfile."""
        db_dp = cls.dbapi.device_profile_get_by_id(context, id)
        obj_dp = cls._from_db_object(cls(context), db_dp)
        return obj_dp
