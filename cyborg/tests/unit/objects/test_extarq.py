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

import six
from unittest import mock

from testtools.matchers import HasLength

from cyborg.common import constants
from cyborg.common import exception
from cyborg import objects
from cyborg.tests.unit.db import base
from cyborg.tests.unit import fake_deployable
from cyborg.tests.unit import fake_device_profile
from cyborg.tests.unit import fake_extarq


class TestExtARQObject(base.DbTestCase):

    def setUp(self):
        super(TestExtARQObject, self).setUp()
        self.fake_db_extarqs = fake_extarq.get_fake_db_extarqs()
        self.fake_obj_extarqs = fake_extarq.get_fake_extarq_objs()
        self.fake_obj_fpga_extarqs = fake_extarq.get_fake_fpga_extarq_objs()
        self.deployable_uuids = ['0acbf8d6-e02a-4394-aae3-57557d209498']

    @mock.patch('cyborg.objects.ExtARQ._from_db_object')
    def test_get(self, mock_from_db_obj):
        db_extarq = self.fake_db_extarqs[0]
        uuid = db_extarq['uuid']
        mock_from_db_obj.return_value = self.fake_obj_extarqs[0]
        with mock.patch.object(self.dbapi, 'extarq_get',
                               autospec=True) as mock_extarq_get:
            mock_extarq_get.return_value = db_extarq
            obj_extarq = objects.ExtARQ.get(self.context, uuid)
            mock_extarq_get.assert_called_once_with(self.context, uuid)
            self.assertEqual(obj_extarq.arq.uuid, uuid)

    @mock.patch('cyborg.objects.ExtARQ._from_db_object')
    def test_list(self, mock_from_db_obj):
        db_extarq = self.fake_db_extarqs[0]
        mock_from_db_obj.return_value = self.fake_obj_extarqs[0]
        with mock.patch.object(self.dbapi, 'extarq_list',
                               autospec=True) as mock_get_list:
            mock_get_list.return_value = [db_extarq]
            obj_extarqs = objects.ExtARQ.list(self.context)
            self.assertEqual(1, mock_get_list.call_count)
            self.assertThat(obj_extarqs, HasLength(1))
            self.assertIsInstance(obj_extarqs[0], objects.ExtARQ)
            for obj_extarq in obj_extarqs:
                self.assertEqual(obj_extarqs[0].arq.uuid, db_extarq['uuid'])

    @mock.patch('cyborg.objects.ExtARQ._from_db_object')
    def test_create(self, mock_from_db_obj):
        db_extarq = self.fake_db_extarqs[0]
        mock_from_db_obj.return_value = self.fake_obj_extarqs[0]
        with mock.patch.object(self.dbapi, 'extarq_create',
                               autospec=True) as mock_extarq_create:
            mock_extarq_create.return_value = db_extarq
            extarq = objects.ExtARQ(self.context, **db_extarq)
            extarq.arq = objects.ARQ(self.context, **db_extarq)
            extarq.create(self.context)
            mock_extarq_create.assert_called_once()

    @mock.patch('openstack.connection.Connection')
    @mock.patch('cyborg.common.nova_client.NovaAPI.notify_binding')
    @mock.patch('cyborg.objects.ExtARQ.bind')
    @mock.patch('cyborg.objects.ExtARQ.get')
    def test_apply_patch_to_bad_arq_state(
            self, mock_get, mock_bind, mock_notify_bind, mock_conn):
        good_states = constants.ARQ_STATES_TRANSFORM_MATRIX[
            constants.ARQ_BIND_STARTED]
        mock_get.return_value = obj_extarq = self.fake_obj_extarqs[0]
        uuid = obj_extarq.arq.uuid
        instance_uuid = obj_extarq.arq.instance_uuid
        valid_fields = {
            uuid: {'hostname': obj_extarq.arq.hostname,
                   'device_rp_uuid': obj_extarq.arq.device_rp_uuid,
                   'instance_uuid': instance_uuid}
            }
        patch_list = {
            str(uuid): [
                {"path": "/hostname", "op": "add",
                 "value": obj_extarq.arq.hostname},
                {"path": "/device_rp_uuid", "op": "add",
                 "value": obj_extarq.arq.device_rp_uuid},
                {"path": "/instance_uuid", "op": "add",
                 "value": instance_uuid}
            ]
        }

        for state in set(constants.ARQ_STATES) - set(good_states):
            obj_extarq.arq.state = state
            mock_get.return_value = obj_extarq
            self.assertRaises(
                exception.ARQInvalidState, objects.ExtARQ.apply_patch,
                self.context, patch_list, valid_fields)

        mock_notify_bind.assert_not_called()

    @mock.patch('cyborg.objects.extarq.ext_arq_job.ExtARQJobMixin.'
                'get_arq_bind_statuses')
    @mock.patch('openstack.connection.Connection')
    @mock.patch('cyborg.common.nova_client.NovaAPI.notify_binding')
    @mock.patch('cyborg.objects.ExtARQ._allocate_attach_handle')
    @mock.patch('cyborg.objects.ExtARQ.get')
    @mock.patch('cyborg.objects.ExtARQ.list')
    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    @mock.patch('cyborg.objects.deployable.Deployable.get_by_device_rp_uuid')
    def test_apply_patch_for_common_extarq(
        self, mock_get_dep, mock_check_state, mock_list, mock_get,
        mock_attach_handle, mock_notify_bind, mock_conn, mock_get_bind_st):

        good_states = constants.ARQ_STATES_TRANSFORM_MATRIX[
            constants.ARQ_BIND_STARTED]
        obj_extarq = self.fake_obj_extarqs[0]
        obj_extarq.arq.state = good_states[0]

        # NOTE(Sundar): Since update_check_state is mocked, ARQ state
        # remains as 'Initial'. So, we mock get_arq_bind_statuses to
        # prevent that from raising exception.
        mock_get_bind_st.return_value = [
            (obj_extarq.arq.uuid, constants.ARQ_BIND_STATUS_FINISH)]

        # TODO(Shaohe) we should control the state of arq to make
        # better testcase.
        # bound_extarq = copy.deepcopy(obj_extarq)
        # bound_extarq.arq.state = constants.ARQ_BOUND
        # mock_get.side_effect = [obj_extarq, bound_extarq]
        mock_get.side_effect = [obj_extarq] * 2
        mock_list.return_value = [obj_extarq]
        uuid = obj_extarq.arq.uuid
        instance_uuid = obj_extarq.arq.instance_uuid

        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(self.context,
                                                       uuid=dep_uuid)
        mock_get_dep.return_value = fake_dep
        valid_fields = {
            uuid: {'hostname': obj_extarq.arq.hostname,
                   'device_rp_uuid': obj_extarq.arq.device_rp_uuid,
                   'instance_uuid': instance_uuid}
            }
        patch_list = {
            str(uuid): [
                {"path": "/hostname", "op": "add",
                 "value": obj_extarq.arq.hostname},
                {"path": "/device_rp_uuid", "op": "add",
                 "value": obj_extarq.arq.device_rp_uuid},
                {"path": "/instance_uuid", "op": "add",
                 "value": instance_uuid}
            ]
        }
        objects.ExtARQ.apply_patch(self.context, patch_list, valid_fields)
        # NOTE(Shaohe) we set the fake_obj_extarqs state is ARQ_INITIAL
        # TODO(Shaohe) we should control the state of arq to make
        # complete status testcase.
        self.assertEqual(obj_extarq.arq.state, 'Initial')
        mock_notify_bind.assert_called_once_with(
            instance_uuid,
            [(obj_extarq.arq.uuid, constants.ARQ_BIND_STATUS_FINISH)])

    @mock.patch('cyborg.objects.extarq.ext_arq_job.ExtARQJobMixin.'
                'get_arq_bind_statuses')
    @mock.patch('openstack.connection.Connection')
    @mock.patch('cyborg.common.nova_client.NovaAPI.notify_binding')
    @mock.patch('cyborg.objects.ExtARQ._allocate_attach_handle')
    @mock.patch('cyborg.objects.ExtARQ.get')
    @mock.patch('cyborg.objects.ExtARQ.list')
    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    @mock.patch('cyborg.objects.deployable.Deployable.get_by_device_rp_uuid')
    @mock.patch('cyborg.common.utils.ThreadWorks.spawn')
    def test_apply_patch_start_fpga_arq_job(
        self, mock_spawn, mock_get_dep, mock_check_state, mock_list, mock_get,
        mock_attach_handle, mock_notify_bind, mock_conn, mock_get_bind_st):
        good_states = constants.ARQ_STATES_TRANSFORM_MATRIX[
            constants.ARQ_BIND_STARTED]
        obj_extarq = self.fake_obj_extarqs[2]
        obj_fpga_extarq = self.fake_obj_fpga_extarqs[1]
        obj_fpga_extarq.state = self.fake_obj_fpga_extarqs[1]
        obj_extarq.arq.state = good_states[0]
        obj_fpga_extarq.arq.state = good_states[0]

        # TODO(Shaohe) we should control the state of arq to make
        # better testcase.
        # bound_extarq = copy.deepcopy(obj_extarq)
        # bound_extarq.arq.state = constants.ARQ_BOUND
        # mock_get.side_effect = [obj_extarq, bound_extarq]
        mock_get.side_effect = [obj_extarq, obj_fpga_extarq]
        mock_list.return_value = [obj_extarq]
        uuid = obj_extarq.arq.uuid
        instance_uuid = obj_extarq.arq.instance_uuid
        # mock_job_get_ext_arq.side_effect = obj_extarq
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(self.context,
                                                       uuid=dep_uuid)
        mock_get_bind_st.return_value = [
            (obj_extarq.arq.uuid, constants.ARQ_BIND_STATUS_FINISH)]
        mock_get_dep.return_value = fake_dep
        mock_spawn.return_value = None
        valid_fields = {
            uuid: {'hostname': obj_extarq.arq.hostname,
                   'device_rp_uuid': obj_extarq.arq.device_rp_uuid,
                   'instance_uuid': instance_uuid}
            }
        patch_list = {
            str(uuid): [
                {"path": "/hostname", "op": "add",
                 "value": obj_extarq.arq.hostname},
                {"path": "/device_rp_uuid", "op": "add",
                 "value": obj_extarq.arq.device_rp_uuid},
                {"path": "/instance_uuid", "op": "add",
                 "value": instance_uuid}
            ]
        }
        objects.ExtARQ.apply_patch(self.context, patch_list, valid_fields)
        # NOTE(Shaohe) we set the fake_obj_extarqs state is ARQ_INITIAL
        # TODO(Shaohe) we should control the state of arq to make
        # better testcase.
        self.assertEqual(obj_extarq.arq.state, 'Initial')
        mock_notify_bind.assert_called_once_with(
            instance_uuid,
            [(obj_extarq.arq.uuid, constants.ARQ_BIND_STATUS_FINISH)])
        # NOTE(Shaohe) check it spawn to start a job.
        mock_spawn.assert_called_once_with(
            obj_fpga_extarq.bind, self.context, fake_dep)

    @mock.patch('openstack.connection.Connection')
    @mock.patch('cyborg.common.nova_client.NovaAPI.notify_binding')
    @mock.patch('cyborg.objects.ExtARQ._allocate_attach_handle')
    @mock.patch('cyborg.objects.ExtARQ.get')
    @mock.patch('cyborg.objects.ExtARQ.list')
    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    @mock.patch('cyborg.objects.deployable.Deployable.get_by_device_rp_uuid')
    @mock.patch('cyborg.common.utils.ThreadWorks.spawn_master')
    def test_apply_patch_fpga_arq_monitor_job(
        self, mock_master, mock_get_dep, mock_check_state, mock_list,
        mock_get, mock_attach_handle, mock_notify_bind, mock_conn):

        good_states = constants.ARQ_STATES_TRANSFORM_MATRIX[
            constants.ARQ_BIND_STARTED]
        obj_extarq = self.fake_obj_extarqs[2]
        obj_fpga_extarq = self.fake_obj_fpga_extarqs[1]
        obj_fpga_extarq.state = self.fake_obj_fpga_extarqs[1]
        obj_extarq.arq.state = good_states[0]
        obj_fpga_extarq.arq.state = good_states[0]

        # TODO(Shaohe) we should control the state of arq to make
        # better testcase.
        # bound_extarq = copy.deepcopy(obj_extarq)
        # bound_extarq.arq.state = constants.ARQ_BOUND
        # mock_get.side_effect = [obj_extarq, bound_extarq]
        mock_get.side_effect = [obj_extarq, obj_fpga_extarq]
        mock_list.return_value = [obj_extarq]
        uuid = obj_extarq.arq.uuid
        instance_uuid = obj_extarq.arq.instance_uuid
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(self.context,
                                                       uuid=dep_uuid)
        mock_get_dep.return_value = fake_dep
        valid_fields = {
            uuid: {'hostname': obj_extarq.arq.hostname,
                   'device_rp_uuid': obj_extarq.arq.device_rp_uuid,
                   'instance_uuid': instance_uuid}
            }
        patch_list = {
            str(uuid): [
                {"path": "/hostname", "op": "add",
                 "value": obj_extarq.arq.hostname},
                {"path": "/device_rp_uuid", "op": "add",
                 "value": obj_extarq.arq.device_rp_uuid},
                {"path": "/instance_uuid", "op": "add",
                 "value": instance_uuid}
            ]
        }
        objects.ExtARQ.apply_patch(self.context, patch_list, valid_fields)
        mock_master.assert_called_once()

    @mock.patch('cyborg.objects.ExtARQ.get')
    @mock.patch('cyborg.objects.ExtARQ._from_db_object')
    def test_destroy(self, mock_from_db_obj, mock_obj_extarq):
        db_extarq = self.fake_db_extarqs[0]
        uuid = db_extarq['uuid']
        mock_from_db_obj.return_value = db_extarq
        mock_obj_extarq.return_value = self.fake_obj_extarqs[0]
        with mock.patch.object(self.dbapi, 'extarq_get',
                               autospec=True) as mock_extarq_get:
            mock_extarq_get.return_value = db_extarq
            with mock.patch.object(self.dbapi, 'extarq_delete',
                                   autospec=True) as mock_extarq_delete:
                extarq = objects.ExtARQ.get(self.context, uuid)
                extarq.destroy(self.context)
                mock_extarq_delete.assert_called_once_with(self.context, uuid)

    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    def test_allocate_attach_handle(self, mock_check_state):
        obj_extarq = self.fake_obj_extarqs[0]
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(self.context,
                                                       uuid=dep_uuid)
        self.assertRaises(
            exception.ResourceNotFound,
            obj_extarq._allocate_attach_handle, self.context, fake_dep)
        mock_check_state.assert_called_once_with(
            self.context, constants.ARQ_BIND_FAILED)

    @mock.patch('logging.LoggerAdapter.error')
    @mock.patch('cyborg.objects.attach_handle.AttachHandle.allocate')
    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    def test_allocate_attach_handle_with_error_log(
        self, mock_check_state, mock_allocate, mock_log):
        obj_extarq = self.fake_obj_extarqs[0]
        dep_uuid = self.deployable_uuids[0]
        e = exception.ResourceNotFound(
            resource='AttachHandle', msg="Just for Test")
        msg = ("Failed to allocate attach handle for ARQ %s"
               "from deployable %s. Reason: %s")
        mock_allocate.side_effect = e
        fake_dep = fake_deployable.fake_deployable_obj(self.context,
                                                       uuid=dep_uuid)
        self.assertRaises(
            exception.ResourceNotFound,
            obj_extarq._allocate_attach_handle, self.context, fake_dep)
        mock_log.assert_called_once_with(
            msg, obj_extarq.arq.uuid, fake_dep.uuid, six.text_type(e))

    @mock.patch('cyborg.objects.ExtARQ.get')
    @mock.patch('cyborg.objects.ExtARQ._from_db_object')
    def test_save(self, mock_from_db_obj, mock_obj_extarq):
        db_extarq = self.fake_db_extarqs[0]
        uuid = db_extarq['uuid']
        mock_from_db_obj.return_value = db_extarq
        mock_obj_extarq.return_value = self.fake_obj_extarqs[0]
        with mock.patch.object(self.dbapi, 'extarq_update',
                               autospec=True) as mock_extarq_update:
            obj_extarq = objects.ExtARQ.get(self.context, uuid)
            obj_extarq.arq.hostname = 'newtestnode1'
            fake_arq_updated = db_extarq
            fake_arq_updated['hostname'] = obj_extarq.arq.hostname
            mock_extarq_update.return_value = fake_arq_updated
            obj_extarq.save(self.context)
            mock_extarq_update.assert_called_once()

    def test_get_arq_bind_statuses(self):
        # ARQ state is 'Bound'  by default in the fake extarqs
        arq_list = [extarq.arq for extarq in self.fake_obj_extarqs]
        bind_status = constants.ARQ_BIND_STATES_STATUS_MAP[
            constants.ARQ_BOUND]
        expected = [(arq.uuid, bind_status) for arq in arq_list]

        result = objects.ExtARQ.get_arq_bind_statuses(arq_list)

        self.assertEqual(expected, result)

    def _test_get_arq_bind_statuses_exception(self):
        extarqs = fake_extarq.get_fake_extarq_objs()
        arq_list = [extarq.arq for extarq in extarqs]
        for arq in arq_list:
            arq['state'] = constants.ARQ_INITIAL

        self.assertRaises(exception.ARQBadState,
                          objects.ExtARQ.get_arq_bind_statuses, arq_list)

    @mock.patch('cyborg.objects.device_profile.DeviceProfile.get_by_name')
    @mock.patch('cyborg.objects.deployable.Deployable.get_by_id')
    @mock.patch('cyborg.db.sqlalchemy.api.Connection.'
                'attach_handle_get_by_id')
    @mock.patch('cyborg.db.sqlalchemy.api.Connection.'
                'device_profile_get_by_id')
    def test_fill_obj_extarq_fields(self, mock_get_devprof, mock_get_ah,
                                    mock_get_obj_dep, mock_obj_devprof):
        in_db_extarq = self.fake_db_extarqs[0]
        # Since state is not 'Bound', attach_handle_get_by_id is not called.
        in_db_extarq['state'] = 'Initial'
        in_db_extarq['deployable_id'] = None
        db_devprof = fake_device_profile.get_db_devprofs()[0]
        obj_devprof = fake_device_profile.get_obj_devprofs()[0]

        mock_get_devprof.return_value = db_devprof
        mock_obj_devprof.return_value = obj_devprof

        out_db_extarq = objects.ExtARQ._fill_obj_extarq_fields(
            self.context, in_db_extarq)

        self.assertEqual(out_db_extarq['device_profile_name'],
                         db_devprof['name'])
        self.assertEqual(out_db_extarq['attach_handle_type'], '')
        self.assertEqual(out_db_extarq['attach_handle_info'], '')
        self.assertEqual(
            out_db_extarq['deployable_uuid'],
            '00000000-0000-0000-0000-000000000000')
        devprof_group_id = out_db_extarq['device_profile_group_id']
        self.assertEqual(out_db_extarq['device_profile_group'],
                         obj_devprof['groups'][devprof_group_id])
