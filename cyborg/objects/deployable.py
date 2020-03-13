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

from oslo_log import log as logging
from oslo_versionedobjects import base as object_base

from cyborg.db import api as dbapi
from cyborg.objects import base
from cyborg.objects import fields as object_fields

LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class Deployable(base.CyborgObject, object_base.VersionedObjectDictCompat):
    # 1.0: Initial version
    # 1.1: Added rp_uuid, driver_name, bitstream_id, num_accel_in_use
    VERSION = '1.1'

    dbapi = dbapi.get_instance()

    fields = {
        'id': object_fields.IntegerField(nullable=False),
        'uuid': object_fields.UUIDField(nullable=False),
        'parent_id': object_fields.IntegerField(nullable=True),
        # parent_id refers to the id of the deployable's parent node
        'root_id': object_fields.IntegerField(nullable=True),
        # root_id refers to the id of the deployable's root to for nested tree
        'name': object_fields.StringField(nullable=False),
        # name of the deployable
        'num_accelerators': object_fields.IntegerField(nullable=False),
        # number of accelerators spawned by this deployable
        'device_id': object_fields.IntegerField(nullable=False),
        # Foreign key constrain to reference device table
        'driver_name': object_fields.StringField(nullable=True),
        # Will change it to non-nullable after other driver report it.
        'rp_uuid': object_fields.UUIDField(nullable=True),
        # UUID of the Resource provider corresponding to this deployable
        'bitstream_id': object_fields.UUIDField(nullable=True),
    }

    def _get_parent_root_id(self, context):
        obj_dep = Deployable.get_by_id(context, self.parent_id)
        return obj_dep.root_id

    def create(self, context):
        """Create a Deployable record in the DB."""

        # FIXME: Add parent_uuid and root_uuid constrains when DB change to
        # parent_uuid & root_uuid

        values = self.obj_get_changes()
        db_dep = self.dbapi.deployable_create(context, values)
        self._from_db_object(self, db_dep)
        self.obj_reset_changes()

    @classmethod
    def get(cls, context, uuid):
        """Find a DB Deployable and return an Obj Deployable."""
        db_dep = cls.dbapi.deployable_get(context, uuid)
        obj_dep = cls._from_db_object(cls(context), db_dep)
        obj_dep.obj_reset_changes()
        return obj_dep

    @classmethod
    def get_by_id(cls, context, id):
        """Find a DB Deployable and return an Obj Deployable."""
        dpl_query = {"id": id}
        obj_dep = Deployable.get_by_filter(context, dpl_query)[0]
        obj_dep.obj_reset_changes()
        return obj_dep

    @classmethod
    def get_by_device_rp_uuid(cls, context, devrp_uuid):
        db_dep = cls.dbapi.deployable_get_by_rp_uuid(context, devrp_uuid)
        obj_dep = cls._from_db_object(cls(context), db_dep)
        return obj_dep

    @classmethod
    def list(cls, context, filters=None):
        """Return a list of Deployable objects."""
        if filters:
            sort_dir = filters.pop('sort_dir', 'desc')
            sort_key = filters.pop('sort_key', 'created_at')
            limit = filters.pop('limit', None)
            marker = filters.pop('marker_obj', None)
            db_deps = cls.dbapi.deployable_get_by_filters(context, filters,
                                                          sort_dir=sort_dir,
                                                          sort_key=sort_key,
                                                          limit=limit,
                                                          marker=marker)
        else:
            db_deps = cls.dbapi.deployable_list(context)
        obj_dpl_list = cls._from_db_object_list(db_deps, context)
        return obj_dpl_list

    def save(self, context):
        """Update a Deployable record in the DB."""
        updates = self.obj_get_changes()
        # TODO(Xinran): Will remove this if find some better way.
        updates.pop("uuid", None)
        updates.pop("created_at", None)
        if "updated_at" in updates.keys() and \
                updates["updated_at"] is not None:
            updates["updated_at"] = updates["updated_at"].replace(tzinfo=None)
        db_dep = self.dbapi.deployable_update(context, self.uuid, updates)
        self.obj_reset_changes()
        self._from_db_object(self, db_dep)

    def update(self, context, updates):
        """Update provided key, value pairs"""
        self.dbapi.deployable_update(context, self.uuid,
                                     updates)

    def destroy(self, context):
        """Delete a Deployable from the DB."""
        self.dbapi.deployable_delete(context, self.uuid)
        self.obj_reset_changes()

    @classmethod
    def get_by_filter(cls, context,
                      filters):
        obj_dpl_list = []
        db_dpl_list = cls.dbapi.deployable_get_by_filters(
            context,
            filters)

        if db_dpl_list:
            for db_dpl in db_dpl_list:
                obj_dpl = cls._from_db_object(cls(context), db_dpl)
                obj_dpl_list.append(obj_dpl)

        return obj_dpl_list

    @classmethod
    def get_list_by_device_id(cls, context, device_id):
        dep_filter = {'device_id': device_id}
        dep_obj_list = Deployable.list(context, dep_filter)
        return dep_obj_list

    @classmethod
    def get_by_name_deviceid(cls, context, name, device_id):
        dep_filter = {'name': name, 'device_id': device_id}
        dep_obj_list = Deployable.list(context, dep_filter)
        if len(dep_obj_list) != 0:
            return dep_obj_list[0]
        else:
            return None

    @classmethod
    def get_by_name(cls, context, name):
        dep_filter = {'name': name}
        dep_obj_list = Deployable.list(context, dep_filter)
        if len(dep_obj_list) != 0:
            return dep_obj_list[0]
        else:
            return None

    def get_cpid_list(self, context):
        query_filter = {"device_id": self.device_id}
        # TODO(Sundar) We should probably get cpid from objects layer,
        # not db layer
        cpid_list = self.dbapi.control_path_get_by_filters(
            context, query_filter)
        return cpid_list
