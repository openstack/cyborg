# Copyright 2019 Intel, Inc.
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

from unittest import mock

from cyborg.common import exception
from cyborg import objects
from cyborg.tests.unit.db import base
from cyborg.tests.unit import fake_device


class TestDeviceObject(base.DbTestCase):

    def setUp(self):
        super(TestDeviceObject, self).setUp()
        self.fake_device = fake_device.get_db_devices()[0]

    def test_get(self):
        uuid = self.fake_device['uuid']
        with mock.patch.object(self.dbapi, 'device_get',
                               autospec=True) as mock_device_get:
            mock_device_get.return_value = self.fake_device
            device = objects.Device.get(self.context, uuid)
            mock_device_get.assert_called_once_with(self.context, uuid)
            self.assertEqual(self.context, device._context)

    def test_get_by_id(self):
        device_id = self.fake_device['id']
        with mock.patch.object(self.dbapi, 'device_get_by_id',
                               autospec=True) as mock_device_get_by_id:
            mock_device_get_by_id.return_value = self.fake_device
            device = objects.Device.get_by_device_id(self.context, device_id)
            mock_device_get_by_id.assert_called_once_with(
                self.context, device_id)
            self.assertEqual(self.context, device._context)

    def test_get_by_non_existed_id(self):
        device_id = self.fake_device['id']
        with mock.patch.object(self.dbapi, 'device_get_by_id',
                               autospec=True) as mock_device_get_by_id:
            mock_device_get_by_id.side_effect = exception.ResourceNotFound(
                resource='Device', msg='with uuid=%s' % device_id)
            self.assertRaises(exception.ResourceNotFound,
                              objects.Device.get_by_device_id,
                              self.context,
                              device_id)

    @mock.patch.object(objects.Device, 'list')
    def test_get_by_hostname(self, mock_list):
        hostname = self.fake_device['hostname']
        dev_filter = {'hostname': hostname}
        mock_list.return_value = [self.fake_device]
        devices = objects.Device.get_list_by_hostname(self.context, hostname)
        mock_list.assert_called_once_with(self.context, dev_filter)
        self.assertEqual(hostname, devices[0]['hostname'])

        # test objects.Device.list return [] when hostname is None.
        mock_list.return_value = []
        hostname = None
        dev_filter = {'hostname': hostname}
        devices = objects.Device.get_list_by_hostname(self.context, hostname)
        mock_list.assert_called_with(self.context, dev_filter)
        self.assertEqual([], devices)

    def test_list(self):
        with mock.patch.object(self.dbapi, 'device_list',
                               autospec=True) as mock_device_list:
            mock_device_list.return_value = [self.fake_device]
            devices = objects.Device.list(self.context)
            self.assertEqual(1, mock_device_list.call_count)
            self.assertEqual(1, len(devices))
            self.assertIsInstance(devices[0], objects.Device)
            self.assertEqual(self.context, devices[0]._context)

    def test_list_with_filter(self):
        with mock.patch.object(self.dbapi, 'device_list_by_filters',
                               autospec=True) as mock_device_with_filter_list:
            mock_device_with_filter_list.return_value = [self.fake_device]
            filters = {'limit': 1}
            devices = objects.Device.list(self.context, filters)
            self.assertEqual(1, mock_device_with_filter_list.call_count)
            self.assertEqual(1, len(devices))
            self.assertIsInstance(devices[0], objects.Device)
            mock_device_with_filter_list.assert_called_once_with(
                self.context,
                {},
                sort_dir='desc',
                sort_key='created_at',
                limit=1,
                marker=None,
                )

    def test_create(self):
        with mock.patch.object(self.dbapi, 'device_create',
                               autospec=True) as mock_device_create:
            mock_device_create.return_value = self.fake_device
            device = objects.Device(self.context,
                                    **self.fake_device)
            device.create(self.context)
            mock_device_create.assert_called_once_with(
                self.context, self.fake_device)
            self.assertEqual(self.context, device._context)

    def test_destroy(self):
        uuid = self.fake_device['uuid']
        with mock.patch.object(self.dbapi, 'device_get',
                               autospec=True) as mock_device_get:
            mock_device_get.return_value = self.fake_device
            with mock.patch.object(self.dbapi, 'device_delete',
                                   autospec=True) as mock_device_delete:
                device = objects.Device.get(self.context, uuid)
                device.destroy(self.context)
                mock_device_delete.assert_called_once_with(self.context,
                                                           uuid)
                self.assertEqual(self.context, device._context)

    def test_update(self):
        uuid = self.fake_device['uuid']
        with mock.patch.object(self.dbapi, 'device_get',
                               autospec=True) as mock_device_get:
            mock_device_get.return_value = self.fake_device
            with mock.patch.object(self.dbapi, 'device_update',
                                   autospec=True) as mock_device_update:
                fake = self.fake_device
                fake["vendor_board_info"] = "new_vendor_board_info"
                mock_device_update.return_value = fake
                device = objects.Device.get(self.context, uuid)
                device.vendor_board_info = 'new_vendor_board_info'
                device.save(self.context)
                mock_device_get.assert_called_once_with(self.context,
                                                        uuid)
                mock_device_update.assert_called_once_with(
                    self.context, uuid,
                    {'vendor_board_info': 'new_vendor_board_info'})
                self.assertEqual(self.context, device._context)

    def test_device_type(self):
        for t in ["GPU", "FPGA", "AICHIP"]:
            device = objects.Device(self.context, type=t)
            self.assertEqual(self.context, device._context)
        # Invaild type will raise ValueError
        self.assertRaises(ValueError, objects.Device,
                          self.context, type='OTHER_TYPE')
