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

from cyborg import objects
from cyborg.common import constants
from cyborg.common import exception
from cyborg.tests.unit import fake_device
from cyborg.tests.unit.db import base


class TestDeviceObject(base.DbTestCase):
    def setUp(self):
        super().setUp()
        self.fake_device = fake_device.get_db_devices()[0]

    def test_get(self):
        uuid = self.fake_device['uuid']
        with mock.patch.object(
            self.dbapi, 'device_get', autospec=True
        ) as mock_device_get:
            mock_device_get.return_value = self.fake_device
            device = objects.Device.get(self.context, uuid)
            mock_device_get.assert_called_once_with(self.context, uuid)
            self.assertEqual(self.context, device._context)

    def test_get_by_id(self):
        device_id = self.fake_device['id']
        with mock.patch.object(
            self.dbapi, 'device_get_by_id', autospec=True
        ) as mock_device_get_by_id:
            mock_device_get_by_id.return_value = self.fake_device
            device = objects.Device.get_by_device_id(self.context, device_id)
            mock_device_get_by_id.assert_called_once_with(
                self.context, device_id
            )
            self.assertEqual(self.context, device._context)

    def test_get_by_non_existed_id(self):
        device_id = self.fake_device['id']
        with mock.patch.object(
            self.dbapi, 'device_get_by_id', autospec=True
        ) as mock_device_get_by_id:
            mock_device_get_by_id.side_effect = exception.ResourceNotFound(
                resource='Device', msg='with uuid=%s' % device_id
            )
            self.assertRaises(
                exception.ResourceNotFound,
                objects.Device.get_by_device_id,
                self.context,
                device_id,
            )

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
        with mock.patch.object(
            self.dbapi, 'device_list', autospec=True
        ) as mock_device_list:
            mock_device_list.return_value = [self.fake_device]
            devices = objects.Device.list(self.context)
            self.assertEqual(1, mock_device_list.call_count)
            self.assertEqual(1, len(devices))
            self.assertIsInstance(devices[0], objects.Device)
            self.assertEqual(self.context, devices[0]._context)

    def test_list_with_filter(self):
        with mock.patch.object(
            self.dbapi, 'device_list_by_filters', autospec=True
        ) as mock_device_with_filter_list:
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
        with mock.patch.object(
            self.dbapi, 'device_create', autospec=True
        ) as mock_device_create:
            mock_device_create.return_value = self.fake_device
            device_dict = fake_device.get_fake_devices_as_dict()[0].copy()
            device_dict.pop('device_state', None)
            device = objects.Device(self.context, **device_dict)
            device.create(self.context)
            expected = device_dict.copy()
            expected['device_state'] = constants.DEVICE_STATE_AVAILABLE
            mock_device_create.assert_called_once_with(self.context, expected)
            self.assertEqual(self.context, device._context)

    def test_create_preserves_explicit_device_state(self):
        with mock.patch.object(
            self.dbapi, 'device_create', autospec=True
        ) as mock_device_create:
            mock_device_create.return_value = self.fake_device
            device_fields = self.fake_device.copy()
            device_fields.pop('device_state', None)
            device = objects.Device(
                self.context,
                **device_fields,
                device_state=constants.DEVICE_STATE_ALLOCATED,
            )
            device.create(self.context)
            expected = self.fake_device.copy()
            expected['device_state'] = constants.DEVICE_STATE_ALLOCATED
            mock_device_create.assert_called_once_with(self.context, expected)

    def test_destroy(self):
        uuid = self.fake_device['uuid']
        with mock.patch.object(
            self.dbapi, 'device_get', autospec=True
        ) as mock_device_get:
            mock_device_get.return_value = self.fake_device
            with mock.patch.object(
                self.dbapi, 'device_delete', autospec=True
            ) as mock_device_delete:
                device = objects.Device.get(self.context, uuid)
                device.destroy(self.context)
                mock_device_delete.assert_called_once_with(self.context, uuid)
                self.assertEqual(self.context, device._context)

    def test_update(self):
        uuid = self.fake_device['uuid']
        with mock.patch.object(
            self.dbapi, 'device_get', autospec=True
        ) as mock_device_get:
            mock_device_get.return_value = self.fake_device
            with mock.patch.object(
                self.dbapi, 'device_update', autospec=True
            ) as mock_device_update:
                fake = self.fake_device
                fake["vendor_board_info"] = "new_vendor_board_info"
                mock_device_update.return_value = fake
                device = objects.Device.get(self.context, uuid)
                device.vendor_board_info = 'new_vendor_board_info'
                device.save(self.context)
                mock_device_get.assert_called_once_with(self.context, uuid)
                mock_device_update.assert_called_once_with(
                    self.context,
                    uuid,
                    {'vendor_board_info': 'new_vendor_board_info'},
                )
                self.assertEqual(self.context, device._context)

    def test_device_type(self):
        for t in constants.DEVICE_TYPE:
            device = objects.Device(self.context, type=t)
            self.assertEqual(self.context, device._context)
        # Invalid type will raise ValueError
        self.assertRaises(
            ValueError, objects.Device, self.context, type='OTHER_TYPE'
        )

    def test_device_state(self):
        for state in [
            'available',
            'allocated',
            'pending_cleaning',
            'cleaning',
            'error',
        ]:
            device = objects.Device(
                self.context, type='NVME', device_state=state
            )
            self.assertEqual(state, device.device_state)
        self.assertRaises(
            ValueError,
            objects.Device,
            self.context,
            type='NVME',
            device_state='invalid',
        )

    def test_supports_cleaning_nvme(self):
        device = objects.Device(self.context, type='NVME')
        self.assertTrue(device.supports_cleaning)

    def test_supports_cleaning_gpu(self):
        device = objects.Device(self.context, type='GPU')
        self.assertFalse(device.supports_cleaning)

    def test_obj_make_compatible_raises_for_mdev_pci(self):
        for type_val in (constants.DEVICE_MDEV, constants.DEVICE_PCI):
            device = objects.Device(self.context, type=type_val)
            self.assertRaises(
                exception.ObjectActionError,
                device.obj_to_primitive,
                target_version='1.2',
            )

    def test_obj_make_compatible_raises_for_nvme(self):
        device = objects.Device(self.context, type=constants.DEVICE_NVME)
        self.assertRaises(
            exception.ObjectActionError,
            device.obj_to_primitive,
            target_version='1.3',
        )

    def test_obj_make_compatible_raises_for_aichip_on_v1_0(self):
        device = objects.Device(self.context, type=constants.DEVICE_AICHIP)
        self.assertRaises(
            exception.ObjectActionError,
            device.obj_to_primitive,
            target_version='1.0',
        )

    def test_obj_make_compatible_removes_status_below_v1_2(self):
        device = objects.Device(
            self.context,
            type=constants.DEVICE_GPU,
            status='maintaining',
        )
        primitive = device.obj_to_primitive()
        device.obj_make_compatible(primitive['cyborg_object.data'], '1.1')
        self.assertNotIn('status', primitive['cyborg_object.data'])

    def test_obj_make_compatible_allows_gpu_on_v1_0(self):
        device = objects.Device(self.context, type=constants.DEVICE_GPU)
        primitive = device.obj_to_primitive(target_version='1.0')
        self.assertEqual(
            constants.DEVICE_GPU, primitive['cyborg_object.data']['type']
        )

    def test_obj_make_compatible_allows_gpu_on_v1_2(self):
        device = objects.Device(self.context, type=constants.DEVICE_GPU)
        primitive = device.obj_to_primitive(target_version='1.2')
        self.assertEqual(
            constants.DEVICE_GPU, primitive['cyborg_object.data']['type']
        )

    def test_obj_make_compatible_drops_device_state(self):
        device = objects.Device(
            self.context, type='NVME', device_state='available'
        )
        primitive = device.obj_to_primitive(target_version='1.4')
        self.assertNotIn('device_state', primitive['cyborg_object.data'])

    def test_from_db_object_heals_null_device_state(self):
        db_device = self.fake_device.copy()
        db_device['device_state'] = None
        with (
            mock.patch.object(
                self.dbapi,
                'deployable_get_by_filters',
                autospec=True,
                return_value=[],
            ) as mock_dep,
            mock.patch.object(
                self.dbapi,
                'device_update',
                autospec=True,
            ) as mock_update,
        ):
            device = objects.Device._from_db_object(
                objects.Device(self.context), db_device
            )
            self.assertEqual(
                constants.DEVICE_STATE_AVAILABLE, device.device_state
            )
            mock_dep.assert_called_once_with(
                self.context, {'device_id': db_device['id']}
            )
            mock_update.assert_called_once_with(
                self.context,
                db_device['uuid'],
                {'device_state': constants.DEVICE_STATE_AVAILABLE},
            )
