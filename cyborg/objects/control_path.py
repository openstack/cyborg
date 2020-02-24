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
from oslo_serialization import jsonutils
from oslo_versionedobjects import base as object_base

from cyborg.common import constants
from cyborg.db import api as dbapi
from cyborg.objects import base
from cyborg.objects import fields as object_fields

LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class ControlpathID(base.CyborgObject, object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    # Version 1.1: Add cpid_info_obj
    VERSION = '1.1'

    dbapi = dbapi.get_instance()

    fields = {
        'id': object_fields.IntegerField(nullable=False),
        'uuid': object_fields.UUIDField(nullable=False),
        'device_id': object_fields.IntegerField(nullable=False),
        'cpid_type': object_fields.EnumField(
            valid_values=constants.CPID_TYPE,
            nullable=False),
        'cpid_info': object_fields.StringField(nullable=False)
    }

    @property
    def cpid_info_obj(self):
        return jsonutils.loads(self.cpid_info)

    @cpid_info_obj.setter
    def cpid_info_obj(self, cpid_info_obj):
        self.cpid_info = jsonutils.dumps(cpid_info_obj)

    def create(self, context):
        """Create a ControlPathID record in the DB."""
        values = self.obj_get_changes()
        db_cp = self.dbapi.control_path_create(context, values)
        self._from_db_object(self, db_cp)

    @classmethod
    def get(cls, context, uuid):
        """Find a DB ControlpathID and return an Obj ControlpathID."""
        db_cp = cls.dbapi.control_path_get_by_uuid(context, uuid)
        obj_cp = cls._from_db_object(cls(context), db_cp)
        return obj_cp

    @classmethod
    def list(cls, context, filters=None):
        """Return a list of ControlpathID objects."""
        if filters:
            sort_dir = filters.pop('sort_dir', 'desc')
            sort_key = filters.pop('sort_key', 'created_at')
            limit = filters.pop('limit', None)
            marker = filters.pop('marker_obj', None)
            db_cps = cls.dbapi.control_path_get_by_filters(context, filters,
                                                           sort_dir=sort_dir,
                                                           sort_key=sort_key,
                                                           limit=limit,
                                                           marker=marker)
        else:
            db_cps = cls.dbapi.control_path_list(context)
        obj_cp_list = cls._from_db_object_list(db_cps, context)
        return obj_cp_list

    def save(self, context):
        """Update an ControlpathID record in the DB"""
        updates = self.obj_get_changes()
        db_cps = self.dbapi.control_path_update(context, self.uuid, updates)
        self._from_db_object(self, db_cps)

    def destroy(self, context):
        """Delete a ControlpathID from the DB."""
        self.dbapi.control_path_delete(context, self.uuid)
        self.obj_reset_changes()

    @classmethod
    def get_by_device_id(cls, context, device_id):
        # control_path is unique for one device.
        cpid_filter = {'device_id': device_id}
        cpid_obj_list = ControlpathID.list(context, cpid_filter)
        if len(cpid_obj_list) != 0:
            return cpid_obj_list[0]
        else:
            return None

    @classmethod
    def get_by_device_id_cpidinfo(cls, context, device_id, cpid_info):
        cpid_filter = {'device_id': device_id,
                       'cpid_info': cpid_info}
        # the list could have one value or is empty.
        cpid_obj_list = ControlpathID.list(context, cpid_filter)
        if len(cpid_obj_list) != 0:
            return cpid_obj_list[0]
        else:
            return None
