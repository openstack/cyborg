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
from cyborg.objects.deployable import Deployable

LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class VirtualFunction(Deployable):
    # Version 1.0: Initial version
    VERSION = '1.0'

    def create(self, context):
        # To ensure the creating type is VF
        if self.type != 'vf':
            raise exception.InvalidDeployType()
        super(VirtualFunction, self).create(context)

    def save(self, context):
        # To ensure the saving type is VF
        if self.type != 'vf':
            raise exception.InvalidDeployType()
        super(VirtualFunction, self).save(context)

    @classmethod
    def get_by_filter(cls, context,
                      filters, sort_key='created_at',
                      sort_dir='desc', limit=None,
                      marker=None, join=None):
        obj_dpl_list = []
        filters['type'] = 'vf'
        db_dpl_list = cls.dbapi.deployable_get_by_filters(context, filters,
                                                          sort_key=sort_key,
                                                          sort_dir=sort_dir,
                                                          limit=limit,
                                                          marker=marker,
                                                          join_columns=join)
        for db_dpl in db_dpl_list:
            obj_dpl = cls._from_db_object(cls(context), db_dpl)
            obj_dpl_list.append(obj_dpl)
        return obj_dpl_list
