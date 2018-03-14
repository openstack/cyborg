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
from cyborg.objects.deployable import Deployable
from cyborg.objects.virtual_function import VirtualFunction

LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class PhysicalFunction(Deployable):
    # Version 1.0: Initial version
    VERSION = '1.0'
    virtual_function_list = []

    def create(self, context):
        # To ensure the creating type is PF
        if self.type != 'pf':
            raise exception.InvalidDeployType()
        super(PhysicalFunction, self).create(context)

    def save(self, context):
        """In addition to save the pf, it should also save the
        vfs associated with this pf
        """
        # To ensure the saving type is PF
        if self.type != 'pf':
            raise exception.InvalidDeployType()

        for exist_vf in self.virtual_function_list:
            exist_vf.save(context)
        super(PhysicalFunction, self).save(context)

    def add_vf(self, vf):
        """add a vf object to the virtual_function_list.
        If the vf already exists, it will ignore,
        otherwise, the vf will be appended to the list
        """
        if not isinstance(vf, VirtualFunction) or vf.type != 'vf':
            raise exception.InvalidDeployType()
        for exist_vf in self.virtual_function_list:
            if base.obj_equal_prims(vf, exist_vf):
                LOG.warning("The vf already exists")
                return None
        vf.parent_uuid = self.uuid
        vf.root_uuid = self.root_uuid
        vf_copy = copy.deepcopy(vf)
        self.virtual_function_list.append(vf_copy)

    def delete_vf(self, context, vf):
        """remove a vf from the virtual_function_list
        if the vf does not exist, ignore it
        """
        for idx, exist_vf in self.virtual_function_list:
            if base.obj_equal_prims(vf, exist_vf):
                removed_vf = self.virtual_function_list.pop(idx)
                removed_vf.destroy(context)
                return
        LOG.warning("The removing vf does not exist!")

    def destroy(self, context):
        """Delete a the pf from the DB."""
        del self.virtual_function_list[:]
        super(PhysicalFunction, self).destroy(context)

    @classmethod
    def get(cls, context, uuid):
        """Find a DB Physical Function and return an Obj Physical Function.
        In addition, it will also finds all the Virtual Functions associated
        with this Physical Function and place them in virtual_function_list
        """
        db_pf = cls.dbapi.deployable_get(context, uuid)
        obj_pf = cls._from_db_object(cls(context), db_pf)
        pf_uuid = obj_pf.uuid

        query = {"parent_uuid": pf_uuid, "type": "vf"}
        db_vf_list = cls.dbapi.deployable_get_by_filters(context, query)

        for db_vf in db_vf_list:
            obj_vf = VirtualFunction.get(context, db_vf.uuid)
            obj_pf.virtual_function_list.append(obj_vf)
        return obj_pf

    @classmethod
    def get_by_filter(cls, context,
                      filters, sort_key='created_at',
                      sort_dir='desc', limit=None,
                      marker=None, join=None):
        obj_dpl_list = []
        filters['type'] = 'pf'
        db_dpl_list = cls.dbapi.deployable_get_by_filters(context, filters,
                                                          sort_key=sort_key,
                                                          sort_dir=sort_dir,
                                                          limit=limit,
                                                          marker=marker,
                                                          join_columns=join)
        for db_dpl in db_dpl_list:
            obj_dpl = cls._from_db_object(cls(context), db_dpl)
            query = {"parent_uuid": obj_dpl.uuid}
            vf_get_list = VirtualFunction.get_by_filter(context,
                                                        query)
            obj_dpl.virtual_function_list = vf_get_list
            obj_dpl_list.append(obj_dpl)
        return obj_dpl_list

    @classmethod
    def _from_db_object(cls, obj, db_obj):
        """Converts a physical function to a formal object.

        :param obj: An object of the class.
        :param db_obj: A DB model of the object
        :return: The object of the class with the database entity added
        """
        obj = Deployable._from_db_object(obj, db_obj)
        if cls is PhysicalFunction:
            obj.virtual_function_list = []
        return obj
