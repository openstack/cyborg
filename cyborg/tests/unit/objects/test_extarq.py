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

import mock

from testtools.matchers import HasLength

from cyborg import objects
from cyborg.tests.unit.db import base
from cyborg.tests.unit import fake_extarq


class TestExtARQObject(base.DbTestCase):

    def setUp(self):
        super(TestExtARQObject, self).setUp()
        self.fake_db_extarqs = fake_extarq.get_fake_db_extarqs()
        self.fake_obj_extarqs = fake_extarq.get_fake_extarq_objs()

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
    def test_apply_patch(self, mock_get, mock_bind, mock_notify_bind,
                         mock_conn):
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
        objects.ExtARQ.apply_patch(self.context, patch_list, valid_fields)
        status = 'completed'
        mock_notify_bind.assert_called_once_with(
            instance_uuid, obj_extarq.arq.device_profile_name, status)

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
