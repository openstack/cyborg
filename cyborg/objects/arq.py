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
from oslo_serialization import jsonutils
from oslo_versionedobjects import base as object_base

from cyborg.db import api as dbapi
from cyborg.objects import base
from cyborg.objects import fields as object_fields


LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class ARQ(base.CyborgObject, object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    # 1.1: v2 API and Nova integration
    VERSION = '1.1'

    dbapi = dbapi.get_instance()
    fields = {
        'id': object_fields.IntegerField(nullable=False),
        'uuid': object_fields.UUIDField(nullable=False),
        'state': object_fields.ARQStateField(nullable=False),
        'device_profile_name': object_fields.StringField(nullable=False),
        'device_profile_group_id':
            object_fields.IntegerField(nullable=False),

        # Fields populated by Nova after scheduling for binding
        'hostname': object_fields.StringField(nullable=True),
        'device_rp_uuid': object_fields.StringField(nullable=True),
        'instance_uuid': object_fields.StringField(nullable=True),
        'project_id': object_fields.StringField(nullable=True),

        # Fields populated by Cyborg after binding
        'attach_handle_type': object_fields.StringField(nullable=True),
        'attach_handle_info': object_fields.DictOfStringsField(nullable=True),
    }

    @staticmethod
    def _from_db_object(arq, db_extarq):
        """Converts an ARQ to a formal object.

        :param arq: An object of the class ARQ
        :param db_extarq: A DB model of the object
        :return: The object of the class with the database entity added
        """
        ahi = db_extarq['attach_handle_info']
        if ahi is not None and ahi != '':
            d = jsonutils.loads(ahi)
            db_extarq['attach_handle_info'] = d
        else:
            db_extarq['attach_handle_info'] = {}

        for field in arq.fields:
            arq[field] = db_extarq.get(field)
        arq.obj_reset_changes()
        return arq
