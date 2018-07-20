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

import copy
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
    VERSION = '1.0'

    dbapi = dbapi.get_instance()
    attributes_list = []

    fields = {
        'id': object_fields.IntegerField(nullable=False),
        'uuid': object_fields.UUIDField(nullable=False),
        'name': object_fields.StringField(nullable=False),
        'parent_uuid': object_fields.UUIDField(nullable=True),
        # parent_uuid refers to the id of the VF's parent node
        'root_uuid': object_fields.UUIDField(nullable=True),
        # root_uuid refers to the id of the VF's root which has to be a PF
        'address': object_fields.StringField(nullable=False),
        # if interface_type is pci(/mdev), address is the pci_address(/path)
        'host': object_fields.StringField(nullable=False),
        'board': object_fields.StringField(nullable=False),
        # board refers to a specific acc board type, e.g P100 GPU card
        'vendor': object_fields.StringField(nullable=False),
        'version': object_fields.StringField(nullable=False),
        'type': object_fields.StringField(nullable=False),
        # type of deployable, e.g, pf/vf/*f
        'interface_type': object_fields.StringField(nullable=False),
        # interface to hypervisor(libvirt), e.g, pci/mdev...
        'assignable': object_fields.BooleanField(nullable=False),
        # identify if an accelerator is in use
        'instance_uuid': object_fields.UUIDField(nullable=True),
        # The id of the virtualized accelerator instance
        'availability': object_fields.StringField(nullable=False),
        # identify the state of acc, e.g released/claimed/...
        'accelerator_id': object_fields.IntegerField(nullable=False)
        # Foreign key constrain to reference accelerator table
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
        del self.attributes_list[:]

    @classmethod
    def get(cls, context, uuid):
        """Find a DB Deployable and return an Obj Deployable."""
        db_dep = cls.dbapi.deployable_get(context, uuid)
        obj_dep = cls._from_db_object(cls(context), db_dep)
        # retrieve all the attrobutes for this deployable
        query = {"deployable_id": obj_dep.id}
        attr_get_list = Attribute.get_by_filter(context,
                                                query)
        obj_dep.attributes_list = attr_get_list
        return obj_dep

    @classmethod
    def get_by_host(cls, context, host):
        """Get a Deployable by host."""
        db_deps = cls.dbapi.deployable_get_by_host(context, host)
        obj_dpl_list = cls._from_db_object_list(db_deps, context)
        for obj_dpl in obj_dpl_list:
            query = {"deployable_id": obj_dpl.id}
            attr_get_list = Attribute.get_by_filter(context,
                                                    query)
            obj_dpl.attributes_list = attr_get_list
        return obj_dpl_list

    @classmethod
    def list(cls, context):
        """Return a list of Deployable objects."""
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
        self._from_db_object(self, db_dep)

    def destroy(self, context):
        """Delete a Deployable from the DB."""
        del self.attributes_list[:]
        self.dbapi.deployable_delete(context, self.uuid)
        self.obj_reset_changes()

    def add_attribute(self, attribute):
        """add a attribute object to the attribute_list.
        If the attribute already exists, it will update the value,
        otherwise, the vf will be appended to the list
        """

        for exist_attr in self.attributes_list:
            if base.obj_equal_prims(attribute, exist_attr):
                LOG.warning("The attribute already exists")
                return None
        attribute.deployable_id = self.id
        attribute_copy = copy.deepcopy(attribute)
        self.attributes_list.append(attribute_copy)

    def delete_attribute(self, context, attribute):
        """remove an attribute from the attributes_list
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

    @classmethod
    def _from_db_object(cls, obj, db_obj):
        """Converts a deployable to a formal object.

        :param obj: An object of the class.
        :param db_obj: A DB model of the object
        :return: The object of the class with the database entity added
        """
        obj = base.CyborgObject._from_db_object(obj, db_obj)
        obj.attributes_list = []

        return obj
