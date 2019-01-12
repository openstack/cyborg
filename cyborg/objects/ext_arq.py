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
from oslo_versionedobjects import base as object_base

from cyborg.db import api as dbapi
from cyborg import objects
from cyborg.common import constants
from cyborg.common import exception
from cyborg.objects import base
from cyborg.objects import fields as object_fields


LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class ExtARQ(base.CyborgObject, object_base.VersionedObjectDictCompat):
    """ ExtARQ is a wrapper around ARQ with Cyborg-private fields.
        Each ExtARQ object contains exactly one ARQ object as a field.
        But, in the db layer, ExtARQ and ARQ are represented together
        as a row in a single table. Both share a single UUID.

        ExtARQ version is bumped up either if any of its fields change
        or if the ARQ version changes.
    """
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'arq': object_fields.ObjectField('ARQ'),
        # Cyborg-private fields
        # Left substate open now, fill them out during design/implementation
        # later.
        'substate': object_fields.StringField(nullable=True),
    }

    def create(self, context, device_profile_id=None):
        """Create an ExtARQ record in the DB."""
        if 'device_profile' not in self.arq and not device_profile_id:
            raise exception.ObjectActionError(
                action='create',
                reason='Device profile is required in ARQ')
        self.arq.state = constants.ARQINITIAL
        self.substate = constants.ARQINITIAL
        values = self.obj_get_changes()
        arq_obj = values.pop('arq', None)
        if arq_obj is not None:
            values.update(arq_obj.as_dict())

        # Pass devprof id to db layer, to avoid repeated queries
        if device_profile_id is not None:
            values['device_profile_id'] = device_profile_id

        db_extarq = self.dbapi.extarq_create(context, values)
        self._from_db_object(self, db_extarq)
        return self

    @classmethod
    def get(cls, context, uuid):
        """Find a DB ExtARQ and return an Obj ExtARQ."""
        db_extarq = cls.dbapi.extarq_get(context, uuid)
        obj_arq = objects.ARQ(context)
        obj_extarq = ExtARQ(context)
        obj_extarq['arq'] = obj_arq
        obj_extarq = cls._from_db_object(obj_extarq, db_extarq)
        return obj_extarq

    @classmethod
    def list(cls, context, limit, marker, sort_key, sort_dir):
        """Return a list of ExtARQ objects."""
        db_extarqs = cls.dbapi.extarq_list(context, limit, marker, sort_key,
                                           sort_dir)
        obj_extarq_list = cls._from_db_object_list(db_extarqs, context)
        return obj_extarq_list

    def save(self, context):
        """Update an ExtARQ record in the DB."""
        updates = self.obj_get_changes()
        db_extarq = self.dbapi.extarq_update(context, self.arq.uuid, updates)
        self._from_db_object(self, db_extarq)

    def destroy(self, context):
        """Delete an ExtARQ from the DB."""
        self.dbapi.extarq_delete(context, self.arq.uuid)
        self.obj_reset_changes()

    def bind(self, context, host_name, devrp_uuid, instance_uuid):
        """ Given a device rp UUID, get the deployable UUID and
            an attach handle.
        """
        # For the fake device, we just set the state to 'Bound'
        # TODO(wangzhh): Move bind logic and unbind logic to the agent later.
        arq = self.arq
        arq.host_name = host_name
        arq.device_rp_uuid = devrp_uuid
        arq.instance_uuid = instance_uuid
        arq.state = constants.ARQBOUND

        self.save(context)

    def unbind(self, context):
        arq = self.arq
        arq.host_name = ''
        arq.device_rp_uuid = ''
        arq.instance_uuid = ''
        arq.state = constants.ARQUNBOUND

        self.save(context)

    @staticmethod
    def _from_db_object(extarq, db_extarq):
        """Converts an ExtARQ to a formal object.

        :param extarq: An object of the class ExtARQ
        :param db_extarq: A DB model of the object
        :return: The object of the class with the database entity added
        """
        for field in extarq.fields:
            if field != 'arq':
                extarq[field] = db_extarq[field]
        extarq.arq = objects.ARQ()
        extarq.arq._from_db_object(extarq.arq, db_extarq)
        extarq.obj_reset_changes()
        return extarq

    def obj_get_changes(self):
        """Returns a dict of changed fields and their new values."""
        changes = {}
        for key in self.obj_what_changed():
            if key != 'arq':
                changes[key] = getattr(self, key)

        for key in self.arq.obj_what_changed():
            changes[key] = getattr(self.arq, key)

        return changes
