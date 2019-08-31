# Copyright 2019 Intel, Inc.
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

from cyborg.common import constants
from cyborg.db import api as dbapi
from cyborg.objects import base
from cyborg.objects import fields as object_fields

LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class AttachHandle(base.CyborgObject, object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': object_fields.IntegerField(nullable=False),
        'uuid': object_fields.UUIDField(nullable=False),
        'deployable_id': object_fields.IntegerField(nullable=False),
        'cpid_id': object_fields.IntegerField(nullable=False),
        'attach_type': object_fields.EnumField(
            valid_values=constants.ATTACH_HANDLE_TYPES,
            nullable=False),
        # attach_info should be JSON here.
        'attach_info': object_fields.StringField(nullable=False),
        'in_use': object_fields.BooleanField(nullable=False, default=False)
    }

    def create(self, context):
        """Create a AttachHandle record in the DB."""
        values = self.obj_get_changes()
        db_ah = self.dbapi.attach_handle_create(context, values)
        self._from_db_object(self, db_ah)

    @classmethod
    def get(cls, context, uuid):
        """Find a DB AttachHandle and return an Obj AttachHandle."""
        db_ah = cls.dbapi.attach_handle_get_by_uuid(context, uuid)
        obj_ah = cls._from_db_object(cls(context), db_ah)
        return obj_ah

    @classmethod
    def get_by_id(cls, context, id):
        """Find a DB AttachHandle by ID and return an Obj AttachHandle."""
        db_ah = cls.dbapi.attach_handle_get_by_id(context, id)
        obj_ah = cls._from_db_object(cls(context), db_ah)
        return obj_ah

    @classmethod
    def list(cls, context, filters=None):
        """Return a list of AttachHandle objects."""
        if filters:
            sort_dir = filters.pop('sort_dir', 'desc')
            sort_key = filters.pop('sort_key', 'created_at')
            limit = filters.pop('limit', None)
            marker = filters.pop('marker_obj', None)
            db_ahs = cls.dbapi.attach_handle_get_by_filters(context, filters,
                                                            sort_dir=sort_dir,
                                                            sort_key=sort_key,
                                                            limit=limit,
                                                            marker=marker)
        else:
            db_ahs = cls.dbapi.attach_handle_list(context)
        obj_ah_list = cls._from_db_object_list(db_ahs, context)
        return obj_ah_list

    def save(self, context):
        """Update an AttachHandle record in the DB"""
        updates = self.obj_get_changes()
        db_ahs = self.dbapi.attach_handle_update(context, self.uuid, updates)
        self._from_db_object(self, db_ahs)

    def destroy(self, context):
        """Delete a AttachHandle from the DB."""
        self.dbapi.attach_handle_delete(context, self.uuid)
        self.obj_reset_changes()

    @classmethod
    def get_ah_list_by_deployable_id(cls, context, deployable_id):
        ah_filter = {'deployable_id': deployable_id}
        ah_obj_list = AttachHandle.list(context, ah_filter)
        return ah_obj_list

    @classmethod
    def get_ah_by_depid_attachinfo(cls, context, deployable_id, attach_info):
        ah_filter = {'deployable_id': deployable_id,
                     'attach_info': attach_info}
        ah_obj_list = AttachHandle.list(context, ah_filter)
        if len(ah_obj_list) != 0:
            return ah_obj_list[0]
        else:
            return None

    @classmethod
    def allocate(cls, context, deployable_id):
        db_ah = cls.dbapi.attach_handle_allocate(context, deployable_id)
        obj_ah = cls._from_db_object(cls(context), db_ah)
        return obj_ah

    def deallocate(self, context):
        values = {"in_use": False}
        self.dbapi.attach_handle_update(context, self.uuid, values)
