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
from oslo_serialization import jsonutils
from oslo_versionedobjects import base as object_base

from cyborg.agent.rpcapi import AgentAPI
from cyborg.common import constants
from cyborg.common import exception
from cyborg.common import nova_client
from cyborg.common import placement_client
from cyborg.conf import CONF
from cyborg.db import api as dbapi
from cyborg import objects
from cyborg.objects.attach_handle import AttachHandle
from cyborg.objects import base
from cyborg.objects.deployable import Deployable
from cyborg.objects.device_profile import DeviceProfile
from cyborg.objects import fields as object_fields

LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class ExtARQ(base.CyborgObject, object_base.VersionedObjectDictCompat):
    """ExtARQ is a wrapper around ARQ with Cyborg-private fields.
       Each ExtARQ object contains exactly one ARQ object as a field.
       But, in the db layer, ExtARQ and ARQ are represented together
       as a row in a single table. Both share a single UUID.
       ExtARQ version is bumped up either if any of its fields change
       or if the ARQ version changes.
    """
    # Version 1.0: Initial version
    # 1.1: v2 API and Nova integration
    VERSION = '1.1'

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
        # For bound ARQs, we keep the attach handle ID here so that
        # it is easy to deallocate on unbind or delete.
        'attach_handle_id': object_fields.IntegerField(nullable=True),
    }

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
    def get(cls, context, uuid):
        """Find a DB ExtARQ and return an Obj ExtARQ."""
        # TODO() Fix warnings that '' is not an UUID
        db_extarq = cls.dbapi.extarq_get(context, uuid)
        obj_arq = objects.ARQ(context)
        obj_extarq = ExtARQ(context)
        obj_extarq['arq'] = obj_arq
        obj_extarq = cls._from_db_object(obj_extarq, db_extarq, context)
        return obj_extarq

    @classmethod
    def list(cls, context):
        """Return a list of ExtARQ objects."""
        db_extarqs = cls.dbapi.extarq_list(context)
        obj_extarq_list = cls._from_db_object_list(db_extarqs, context)
        return obj_extarq_list

    def save(self, context):
        """Update an ExtARQ record in the DB."""
        updates = self.obj_get_changes()
        db_extarq = self.dbapi.extarq_update(context, self.arq.uuid, updates)
        self._from_db_object(self, db_extarq, context)

    def destroy(self, context):
        """Delete an ExtARQ from the DB."""
        self.dbapi.extarq_delete(context, self.arq.uuid)
        self.obj_reset_changes()

    @classmethod
    def delete_by_uuid(cls, context, arq_uuid_list):
        for uuid in arq_uuid_list:
            obj_extarq = objects.ExtARQ.get(context, uuid)
            # TODO() Defer deletion to conductor
            if obj_extarq.arq.state != constants.ARQ_INITIAL:
                obj_extarq.unbind(context)
            obj_extarq.destroy(context)

    @classmethod
    def delete_by_instance(cls, context, instance_uuid):
        """Delete all ARQs for given instance."""
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

    def _get_bitstream_md_from_function_id(self, function_id):
        """Get bitstream metadata given a function id."""
        conn = self._get_glance_connection()
        properties = {'accel:function_id': function_id}
        resp = conn.image.get('/images', params=properties)
        if resp:
            image_list = resp.json()['images']
            if type(image_list) != list:
                raise exception.InvalidType(
                    obj='image', type=type(image_list),
                    expected='list')
            if len(image_list) != 1:
                raise exception.ExpectedOneObject(obj='image',
                                                  count=len(image_list))
            return image_list[0]
        else:
            LOG.warning('Failed to get image for function (%s)',
                        function_id)
            return None

    def _get_bitstream_md_from_bitstream_id(self, bitstream_id):
        """Get bitstream metadata given a bitstream id."""
        conn = self._get_glance_connection()
        resp = conn.image.get('/images/' + bitstream_id)
        if resp:
            return resp.json()
        else:
            LOG.warning('Failed to get image for bitstream (%s)',
                        bitstream_id)
            return None

    def _do_programming(self, context, hostname,
                        deployable, bitstream_id):
        driver_name = deployable.driver_name

        query_filter = {"device_id": deployable.device_id}
        # TODO() We should probably get cpid from objects layer, not db layer
        cpid_list = self.dbapi.control_path_get_by_filters(
            context, query_filter)
        count = len(cpid_list)
        if count != 1:
            raise exception.ExpectedOneObject(type='controlpath_id',
                                              count=count)
        controlpath_id = cpid_list[0]
        controlpath_id['cpid_info'] = jsonutils.loads(
            controlpath_id['cpid_info'])
        LOG.info('Found control path id: %s', controlpath_id.__dict__)

        LOG.info('Starting programming for host: (%s) deployable (%s) '
                 'bitstream_id (%s)', hostname,
                 deployable.uuid, bitstream_id)
        agent = AgentAPI()
        # TODO() do this asynchronously
        # TODO() do this in the conductor
        agent.fpga_program_v2(context, hostname,
                              controlpath_id, bitstream_id,
                              driver_name)
        LOG.info('Finished programming for host: (%s) deployable (%s)',
                 hostname, deployable.uuid)
        # TODO() propagate agent errors to caller
        return True

    def _update_placement(self, devrp_uuid, function_id,
                          bitstream_md, driver_name):
        placement = placement_client.PlacementClient()
        placement.delete_traits_with_prefixes(
            devrp_uuid, ['CUSTOM_FPGA_FUNCTION_ID'])
        # TODO(Sundar) Don't apply function trait if bitstream is private
        if not function_id:
            function_id = bitstream_md.get('accel:function_id')
        if function_id:
            function_id = function_id.upper().replace('-', '_-')
            # TODO(Sundar) Validate this is a valid trait name
            # Assume driver name == vendor name for FPGA driver.
            vendor = driver_name.upper()
            trait_names = ['CUSTOM_FPGA_FUNCTION_ID_' + vendor + function_id]
            placement.add_traits_to_rp(devrp_uuid, trait_names)

    def bind(self, context, hostname, devrp_uuid, instance_uuid):
        """Given a device rp UUID, get the deployable UUID and
           an attach handle.
        """
        LOG.info('[arqs:objs] bind. hostname: %s, devrp_uuid: %s'
                 'instance: %s', hostname, devrp_uuid, instance_uuid)

        bitstream_id = self.device_profile_group.get('accel:bitstream_id')
        function_id = self.device_profile_group.get('accel:function_id')
        programming_needed = (bitstream_id is not None or
                              function_id is not None)
        if (programming_needed and
           bitstream_id is not None and function_id is not None):
            raise exception.InvalidParameterValue(
                'In device profile {0}, only one among bitstream_id '
                'and function_id must be set, but both are set')

        deployable = Deployable.get_by_device_rp_uuid(context, devrp_uuid)

        # TODO() Check that deployable.device.hostname matches param hostname

        # Note(Sundar): We associate the ARQ with instance UUID before the
        # programming starts. So, if programming fails and then Nova calls
        # to delete all ARQs for a given instance, we can still pick all
        # the relevant ARQs.
        arq = self.arq
        arq.hostname = hostname
        arq.device_rp_uuid = devrp_uuid
        arq.instance_uuid = instance_uuid
        # If prog fails, we'll change the state
        arq.state = constants.ARQ_BIND_STARTED
        self.save(context)  # ARQ changes get committed here

        if programming_needed:
            LOG.info('[arqs:objs] bind. Programming needed. '
                     'bitstream: (%s) function: (%s) Deployable UUID: (%s)',
                     bitstream_id or '', function_id or '',
                     deployable.uuid)
            if bitstream_id is not None:  # FPGA aaS
                bitstream_md = self._get_bitstream_md_from_bitstream_id(
                    bitstream_id)
            else:  # Accelerated Function aaS
                bitstream_md = self._get_bitstream_md_from_function_id(
                    function_id)
                LOG.info('[arqs:objs] For function id (%s), got '
                         'bitstream id (%s)', function_id,
                         bitstream_md['id'])
            bitstream_id = bitstream_md['id']

            if deployable.bitstream_id == bitstream_id:
                LOG.info('Deployable %(uuid)s already has the needed '
                         'bitstream %(stream_id)s. Skipping programming.',
                         {"uuid": deployable.uuid, "stream_id": bitstream_id})
            else:
                ok = self._do_programming(context, hostname,
                                          deployable, bitstream_id)
                if ok:
                    self._update_placement(devrp_uuid, function_id,
                                           bitstream_md,
                                           deployable.driver_name)
                    deployable.update(context, {'bitstream_id': bitstream_id})
                    arq.state = constants.ARQ_BOUND
                else:
                    arq.state = constants.ARQ_BIND_FAILED

        # If programming was done, arq.state already got updated.
        # If no programming was needed, transition to BOUND state.
        if arq.state == constants.ARQ_BIND_STARTED:
            arq.state = constants.ARQ_BOUND

        # We allocate attach handle after programming because, if latter
        #   fails, we need to deallocate the AH
        if arq.state == constants.ARQ_BOUND:  # still on happy path
            try:
                ah = AttachHandle.allocate(context, deployable.id)
                self.attach_handle_id = ah.id
            except Exception:
                LOG.error("Failed to allocate attach handle for ARQ "
                          "%(arq_uuid)s from deployable %(deployable_uuid)s",
                          {"arq_uuid": arq.uuid,
                           "deployable_uuid": deployable.uuid})
                arq.state = constants.ARQ_BIND_FAILED

        self.arq = arq
        self.save(context)  # ARQ state changes get committed here

    @classmethod
    def apply_patch(cls, context, patch_list, valid_fields):
        """Apply JSON patch. See api/controllers/v1/arqs.py. """
        device_profile_name = None
        instance_uuid = None
        bind_action = False
        status = "completed"
        for arq_uuid, patch in patch_list.items():
            extarq = ExtARQ.get(context, arq_uuid)
            if not device_profile_name:
                device_profile_name = extarq.arq.device_profile_name
            if not instance_uuid:
                instance_uuid = valid_fields[arq_uuid]['instance_uuid']
            if patch[0]['op'] == 'add':  # All ops are 'add'
                # True if do binding, False if do unbinding.
                bind_action = True
                extarq.bind(context,
                            valid_fields[arq_uuid]['hostname'],
                            valid_fields[arq_uuid]['device_rp_uuid'],
                            valid_fields[arq_uuid]['instance_uuid'])
                if extarq.arq.state == constants.ARQ_BIND_FAILED:
                    status = "failed"
                elif extarq.arq.state == constants.ARQ_BOUND:
                    continue
                else:
                    raise exception.ARQInvalidState(state=extarq.arq.state)
            else:
                bind_action = False
                extarq.unbind(context)
        if bind_action:
            nova_api = nova_client.NovaAPI()
            nova_api.notify_binding(instance_uuid,
                                    device_profile_name, status)

    def unbind(self, context):
        arq = self.arq
        arq.hostname = None
        arq.device_rp_uuid = None
        arq.instance_uuid = None
        arq.state = constants.ARQ_UNBOUND

        # Unbind: mark attach handles as freed
        ah_id = self.attach_handle_id
        if ah_id:
            attach_handle = AttachHandle.get_by_id(context, ah_id)
            attach_handle.deallocate(context)
        self.attach_handle_id = None
        self.save(context)

    @classmethod
    def _fill_obj_extarq_fields(cls, context, db_extarq):
        """ExtARQ object has some fields that are not present
           in db_extarq. We fill them out here.
        """
        # From the 2 fields in the ExtARQ, we obtain other fields.
        devprof_id = db_extarq['device_profile_id']
        devprof_group_id = db_extarq['device_profile_group_id']

        devprof = cls.dbapi.device_profile_get_by_id(context, devprof_id)
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
                    resource='attach handle',
                    msg='')

        # TODO() Get the deployable_uuid
        db_extarq['deployable_uuid'] = ''

        # Get the device profile group
        obj_devprof = DeviceProfile.get_by_name(context, devprof['name'])
        groups = obj_devprof['groups']
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
                extarq[field] = db_extarq[field]
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
