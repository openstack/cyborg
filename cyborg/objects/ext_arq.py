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

from openstack import connection
from oslo_log import log as logging
from oslo_utils import versionutils
from oslo_versionedobjects import base as object_base

from cyborg.common import constants
from cyborg.common.constants import ARQ_STATES_TRANSFORM_MATRIX
from cyborg.common import exception
from cyborg.common import utils
from cyborg.conf import CONF
from cyborg.db import api as dbapi
from cyborg import objects
from cyborg.objects.attach_handle import AttachHandle
from cyborg.objects import base
from cyborg.objects.device_profile import DeviceProfile
from cyborg.objects.extarq.ext_arq_job import ExtARQJobMixin
from cyborg.objects import fields as object_fields


LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class ExtARQ(base.CyborgObject, object_base.VersionedObjectDictCompat,
             utils.FactoryMixin, ExtARQJobMixin):
    """ExtARQ is a wrapper around ARQ with Cyborg-private fields.
       Each ExtARQ object contains exactly one ARQ object as a field.
       But, in the db layer, ExtARQ and ARQ are represented together
       as a row in a single table. Both share a single UUID.
       ExtARQ version is bumped up either if any of its fields change
       or if the ARQ version changes.
    """
    # Version 1.0: Initial version
    # 1.1: v2 API and Nova integration
    # 1.2: Fill the value of deployable_id
    VERSION = '1.2'

    dbapi = dbapi.get_instance()

    fields = {
        'arq': object_fields.ObjectField('ARQ'),
        # Cyborg-private fields
        # Left substate open now, fill them out during design/implementation
        # later.
        'substate': object_fields.StringField(),
        'deployable_uuid': object_fields.UUIDField(nullable=True),

        # The dp group is copied in to the extarq, so that any changes or
        # deletions to the device profile do not affect running VMs.
        'device_profile_group': object_fields.DictOfStringsField(
            nullable=True),
        # For bound ARQs, we keep the attach handle ID and deployable ID here
        # so that it is easy to deallocate on unbind or delete.
        'attach_handle_id': object_fields.IntegerField(nullable=True),
        'deployable_id': object_fields.IntegerField(nullable=True),
    }

    def obj_make_compatible(self, primitive, target_version):
        super(ExtARQ, self).obj_make_compatible(
            primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)
        # TODO(eric): need to handle v1.1 changes
        if target_version < (1, 2) and 'deployable_id' in primitive:
            del primitive['deployable_id']

    def create(self, context, device_profile_id=None):
        """Create an ExtARQ record in the DB."""
        if 'device_profile_name' not in self.arq and not device_profile_id:
            raise exception.ObjectActionError(
                action='create',
                reason='Device profile name is required in ARQ')
        self.arq.state = constants.ARQ_INITIAL
        self.substate = constants.ARQ_INITIAL
        values = self.obj_get_changes()
        arq_obj = values.pop('arq', None)
        if arq_obj is not None:
            values.update(arq_obj.as_dict())

        # Pass devprof id to db layer, to avoid repeated queries
        if device_profile_id is not None:
            values['device_profile_id'] = device_profile_id

        db_extarq = self.dbapi.extarq_create(context, values)
        self._from_db_object(self, db_extarq, context)
        return self

    @classmethod
    def get(cls, context, uuid, lock=False):
        """Find a DB ExtARQ and return an Obj ExtARQ."""
        db_extarq = cls.dbapi.extarq_get(context, uuid)
        obj_arq = objects.ARQ(context)
        obj_extarq = cls(context)
        obj_extarq['arq'] = obj_arq
        obj_extarq = cls._from_db_object(obj_extarq, db_extarq, context)
        return obj_extarq

    @classmethod
    def list(cls, context, uuid_range=None):
        """Return a list of ExtARQ objects."""
        db_extarqs = cls.dbapi.extarq_list(context, uuid_range)
        obj_extarq_list = cls._from_db_object_list(
            db_extarqs, context)
        return obj_extarq_list

    def save(self, context):
        """Update an ExtARQ record in the DB."""
        updates = self.obj_get_changes()
        db_extarq = self.dbapi.extarq_update(context, self.arq.uuid, updates)
        self._from_db_object(self, db_extarq, context)

    def update_state(self, context, state, scope=None):
        """Update an ExtARQ state record in the DB."""
        updates = self.obj_get_changes()
        updates["state"] = state
        db_extarq = self.dbapi.extarq_update(
            context, self.arq.uuid, updates, scope)
        self._from_db_object(self, db_extarq, context)

    def update_check_state(self, context, state, scope=None):
        if self.arq.state == state:
            LOG.info("ExtARQ(%s) state is %s, no need to update",
                     self.arq.uuid, state)
            return False
        old = self.arq.state
        scope = scope or ARQ_STATES_TRANSFORM_MATRIX[state]
        self.update_state(context, state, scope)
        ea = ExtARQ.get(context, self.arq.uuid, lock=True)
        if not ea:
            raise exception.ResourceNotFound(
                resources='ExtARQ',
                msg="Can not find ExtARQ(%s)" % self.arq.uuid)
        current = ea.arq.state
        if state != current:
            msg = ("Failed to change ARQ state from %s to %s, the current "
                   "state is %s" % (old, state, current))
            LOG.error(msg)
            raise exception.ARQBadState(
                state=current, uuid=self.arq.uuid, expected=list(state))
        return True

    def destroy(self, context):
        """Delete an ExtARQ from the DB."""
        self.dbapi.extarq_delete(context, self.arq.uuid)
        self.obj_reset_changes()

    @classmethod
    def delete_by_uuid(cls, context, arq_uuid_list):
        """Delete a list of ARQs based on their UUIDs.

        This is not idempotent, i.e., if the first call to delete an
        ARQ has succeeded, second and later calls to delete the same ARQ
        will get errored out, but it will raise the exception only after
        all input arq being operated.
        """
        unexisted = []
        for uuid in arq_uuid_list:
            try:
                obj_extarq = objects.ExtARQ.get(context, uuid)
                # TODO() Defer deletion to conductor
                if obj_extarq.arq.state != constants.ARQ_INITIAL:
                    obj_extarq.unbind(context)
                obj_extarq.destroy(context)
            except exception.ResourceNotFound:
                unexisted.append(uuid)
                continue
        if unexisted:
            LOG.warning('There are unexisted arqs: %s', unexisted)
            raise exception.ResourceNotFound(
                resource='ARQ',
                msg='with uuids %s' % unexisted)

    @classmethod
    def delete_by_instance(cls, context, instance_uuid):
        """Delete all ARQs for given instance.

        This is idempotent, i.e., it would have the same effect if called
        repeatedly with the same instance UUID. In other words, it would
        not raise an error on the second and later attempts even if the
        first one has deleted the ARQs.
        """
        obj_extarqs = [extarq for extarq in objects.ExtARQ.list(context)
                       if extarq.arq['instance_uuid'] == instance_uuid]
        for obj_extarq in obj_extarqs:
            LOG.info('Deleting obj_extarq uuid %s for instance %s',
                     obj_extarq.arq['uuid'], obj_extarq.arq['instance_uuid'])
            obj_extarq.unbind(context)
            obj_extarq.destroy(context)

    def _get_glance_connection(self):
        default_user = 'devstack-admin'
        try:
            auth_user = CONF.image.username or default_user
        except Exception:
            auth_user = default_user
        return connection.Connection(cloud=auth_user)

    def _allocate_attach_handle(self, context, deployable):
        try:
            ah = AttachHandle.allocate(context, deployable.id)
            self.attach_handle_id = ah.id
        except Exception as e:
            LOG.error("Failed to allocate attach handle for ARQ %s"
                      "from deployable %s. Reason: %s",
                      self.arq.uuid, deployable.uuid, str(e))
            # TODO(Shaohe) Rollback? We have _update_placement,
            # should cancel it.
            self.update_check_state(
                context, constants.ARQ_BIND_FAILED)
            raise
        LOG.info('Attach handle(%s) allocate for ARQ(%s) successfully.',
                 ah.uuid, self.arq.uuid)

    def bind(self, context, deployable):
        self._allocate_attach_handle(context, deployable)
        self.deployable_id = deployable.id
        self.save(context)
        # ARQ state changes get committed here
        self.update_check_state(context, constants.ARQ_BOUND)
        LOG.info('Update ARQ %s state to "Bound" successfully.',
                 self.arq.uuid)
        # TODO(Shaohe) rollback self._unbind and self._delete
        # if (self.arq.state == constants.ARQ_DELETING
        #         or self.arq.state == ARQ_UNBOUND):

    def _deallocate_attach_handle(self, context, ah_id):
        try:
            attach_handle = AttachHandle.get_by_id(context, ah_id)
            attach_handle.deallocate(context)
        except Exception as e:
            LOG.error("Failed to deallocate attach handle %s for ARQ %s."
                      "Reason: %s", ah_id, self.arq.uuid, str(e))
            self.update_check_state(
                context, constants.ARQ_UNBIND_FAILED)
            raise
        LOG.info('Attach handle(%s) deallocate for ARQ(%s) successfully.',
                 ah_id, self.arq.uuid)

    def unbind(self, context):
        arq = self.arq
        arq.hostname = None
        arq.device_rp_uuid = None
        arq.instance_uuid = None
        arq.state = constants.ARQ_UNBOUND

        # Unbind: mark attach handles as freed
        ah_id = self.attach_handle_id
        if ah_id:
            self._deallocate_attach_handle(context, ah_id)
        self.attach_handle_id = None
        self.deployable_id = None
        self.save(context)

    @classmethod
    def _fill_obj_extarq_fields(cls, context, db_extarq):
        """ExtARQ object has some fields that are not present
           in db_extarq. We fill them out here.
        """
        # From the 2 fields in the ExtARQ, we obtain other fields.
        devprof_id = db_extarq['device_profile_id']
        devprof_group_id = db_extarq['device_profile_group_id']

        devprof = DeviceProfile.get_by_id(context, devprof_id)
        db_extarq['device_profile_name'] = devprof['name']

        db_extarq['attach_handle_type'] = ''
        db_extarq['attach_handle_info'] = ''
        if db_extarq['state'] == 'Bound':  # TODO() Do proper bind
            db_ah = cls.dbapi.attach_handle_get_by_id(
                context, db_extarq['attach_handle_id'])
            if db_ah is not None:
                db_extarq['attach_handle_type'] = db_ah['attach_type']
                db_extarq['attach_handle_info'] = db_ah['attach_info']
            else:
                raise exception.ResourceNotFound(
                    resource='Attach Handle',
                    msg='with uuid=%s' % db_extarq['attach_handle_id'])

        if db_extarq['deployable_id']:
            dep = objects.Deployable.get_by_id(context,
                                               db_extarq['deployable_id'])
            db_extarq['deployable_uuid'] = dep.uuid
        else:
            LOG.debug('Setting deployable UUID to zeroes for db_extarq %s',
                      db_extarq['uuid'])
            db_extarq['deployable_uuid'] = (
                '00000000-0000-0000-0000-000000000000')

        groups = devprof['groups']
        db_extarq['device_profile_group'] = groups[devprof_group_id]

        return db_extarq

    @classmethod
    def _from_db_object(cls, extarq, db_extarq, context):
        """Converts an ExtARQ to a formal object.
        :param extarq: An object of the class ExtARQ
        :param db_extarq: A DB model of the object
        :return: The object of the class with the database entity added
        """
        cls._fill_obj_extarq_fields(context, db_extarq)

        for field in extarq.fields:
            if field != 'arq':
                extarq[field] = db_extarq.get(field)
        extarq.arq = objects.ARQ()
        extarq.arq._from_db_object(extarq.arq, db_extarq)
        extarq.obj_reset_changes()
        return extarq

    @classmethod
    def _from_db_object_list(cls, db_objs, context):
        """Converts a list of ExtARQs to a list of formal objects."""
        objs = []
        for db_obj in db_objs:
            extarq = cls(context)
            obj = cls._from_db_object(extarq, db_obj, context)
            objs.append(obj)
        return objs

    def obj_get_changes(self):
        """Returns a dict of changed fields and their new values."""
        changes = {}
        for key in self.obj_what_changed():
            if key != 'arq':
                changes[key] = getattr(self, key)

        for key in self.arq.obj_what_changed():
            changes[key] = getattr(self.arq, key)

        return changes
