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
from cyborg.objects.attribute import Attribute

LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class Deployable(base.CyborgObject, object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '2.0'

    dbapi = dbapi.get_instance()
    attributes_list = []

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
        'device_id': object_fields.IntegerField(nullable=False)
        # Foreign key constrain to reference device table
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
        del self.attributes_list[:]

    @classmethod
    def get(cls, context, uuid, with_attribute_list=True):
        """Find a DB Deployable and return an Obj Deployable."""
        db_dep = cls.dbapi.deployable_get(context, uuid)
        obj_dep = cls._from_db_object(cls(context), db_dep)
        # retrieve all the attributes for this deployable
        if with_attribute_list:
            query = {"deployable_id": obj_dep.id}
            attr_get_list = Attribute.get_by_filter(context,
                                                    query)
            obj_dep.attributes_list = attr_get_list

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
    def list(cls, context, filters={}):
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
        for obj_dpl in obj_dpl_list:
            query = {"deployable_id": obj_dpl.id}
            attr_get_list = Attribute.get_by_filter(context,
                                                    query)
            obj_dpl.attributes_list = attr_get_list
        return obj_dpl_list

    def save(self, context):
        """Update a Deployable record in the DB."""
        updates = self.obj_get_changes()
        db_dep = self.dbapi.deployable_update(context, self.uuid, updates)
        self.obj_reset_changes()
        self._from_db_object(self, db_dep)
        query = {"deployable_id": self.id}
        attr_get_list = Attribute.get_by_filter(context,
                                                query)
        self.attributes_list = attr_get_list

    def destroy(self, context):
        """Delete a Deployable from the DB."""
        del self.attributes_list[:]
        self.dbapi.deployable_delete(context, self.uuid)
        self.obj_reset_changes()

    def add_attribute(self, context, key, value):
        """Add an attribute object to the attribute_list.
        If the attribute already exists, it will update the value,
        otherwise, the attribute will be appended to the list
        """

        for exist_attr in self.attributes_list:
            if key == exist_attr.key:
                LOG.warning("The attribute already exists")
                if value != exist_attr.value:
                    exist_attr.value = value
                    exist_attr.save(context)
                return None
        # The attribute does not exist yet. Create it.
        attr_vals = {
            'deployable_id': self.id,
            'key': key,
            'value': value
        }
        attr = Attribute(context, **attr_vals)
        attr.create(context)
        self.attributes_list.append(attr)

    def delete_attribute(self, context, attribute):
        """Remove an attribute from the attributes_list
        if the attribute does not exist, ignore it
        """

        idx = 0
        for exist_attribute in self.attributes_list:
            if base.obj_equal_prims(attribute, exist_attribute):
                removed_attribute = self.attributes_list.pop(idx)
                removed_attribute.destroy(context)
                return
            idx = idx + 1
        LOG.warning("The removing attribute does not exist!")

    @classmethod
    def get_by_filter(cls, context,
                      filters):
        obj_dpl_list = []
        db_dpl_list = cls.dbapi.deployable_get_by_filters_with_attributes(
            context,
            filters)

        if db_dpl_list:
            for db_dpl in db_dpl_list:
                obj_dpl = cls._from_db_object(cls(context), db_dpl)
                query = {"deployable_id": obj_dpl.id}
                attr_get_list = Attribute.get_by_filter(context,
                                                        query)
                obj_dpl.attributes_list = attr_get_list
                obj_dpl_list.append(obj_dpl)

        return obj_dpl_list

    @staticmethod
    def _from_db_object(obj, db_obj):
        """Converts a deployable to a formal object.

        :param obj: An object of the class.
        :param db_obj: A DB model of the object
        :return: The object of the class with the database entity added
        """
        for field in obj.fields:
            obj[field] = db_obj[field]
        obj.attributes_list = []

        return obj

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
