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

from cyborg.common import exception
from cyborg.db import api as dbapi
from cyborg.objects import base
from cyborg.objects import fields as object_fields


LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class Deployable(base.CyborgObject, object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'uuid': object_fields.UUIDField(nullable=False),
        'name': object_fields.StringField(nullable=False),
        'parent_uuid': object_fields.UUIDField(nullable=True),
        'root_uuid': object_fields.UUIDField(nullable=True),
        'pcie_address': object_fields.StringField(nullable=False),
        'host': object_fields.StringField(nullable=False),
        'board': object_fields.StringField(nullable=False),
        'vendor': object_fields.StringField(nullable=False),
        'version': object_fields.StringField(nullable=False),
        'type': object_fields.StringField(nullable=False),
        'assignable': object_fields.BooleanField(nullable=False),
        'instance_uuid': object_fields.UUIDField(nullable=True),
        'availability': object_fields.StringField(nullable=False),
    }

    def _get_parent_root_uuid(self):
        obj_dep = Deployable.get(None, self.parent_uuid)
        return obj_dep.root_uuid

    def create(self, context):
        """Create a Deployable record in the DB."""
        if 'uuid' not in self:
            raise exception.ObjectActionError(action='create',
                                              reason='uuid is required')

        if self.parent_uuid is None:
            self.root_uuid = self.uuid
        else:
            self.root_uuid = self._get_parent_root_uuid()

        values = self.obj_get_changes()
        db_dep = self.dbapi.deployable_create(context, values)
        self._from_db_object(self, db_dep)

    @classmethod
    def get(cls, context, uuid):
        """Find a DB Deployable and return an Obj Deployable."""
        db_dep = cls.dbapi.deployable_get(context, uuid)
        obj_dep = cls._from_db_object(cls(context), db_dep)
        return obj_dep

    @classmethod
    def get_by_host(cls, context, host):
        """Get a Deployable by host."""
        db_deps = cls.dbapi.deployable_get_by_host(context, host)
        return cls._from_db_object_list(db_deps, context)

    @classmethod
    def list(cls, context):
        """Return a list of Deployable objects."""
        db_deps = cls.dbapi.deployable_list(context)
        return cls._from_db_object_list(db_deps, context)

    def save(self, context):
        """Update a Deployable record in the DB."""
        updates = self.obj_get_changes()
        db_dep = self.dbapi.deployable_update(context, self.uuid, updates)
        self._from_db_object(self, db_dep)

    def destroy(self, context):
        """Delete a Deployable from the DB."""
        self.dbapi.deployable_delete(context, self.uuid)
        self.obj_reset_changes()
