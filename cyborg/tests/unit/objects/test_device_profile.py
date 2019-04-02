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


import mock

from cyborg import objects
from cyborg.tests.unit.db import base
from cyborg.tests.unit.db import utils


class TestDeviceProfileObject(base.DbTestCase):

    def setUp(self):
        super(TestDeviceProfileObject, self).setUp()
        self.fake_device_profile = utils.get_test_device_profile()

    def test_get_by_uuid(self):
        uuid = self.fake_device_profile['uuid']
        with mock.patch.object(self.dbapi, 'device_profile_get_by_uuid',
                               autospec=True) as mock_device_profile_get:
            mock_device_profile_get.return_value = self.fake_device_profile
            device_profile = objects.DeviceProfile.get(self.context, uuid)
            mock_device_profile_get.assert_called_once_with(self.context, uuid)
            self.assertEqual(self.context, device_profile._context)

    def test_get_by_id(self):
        id = self.fake_device_profile['id']
        with mock.patch.object(self.dbapi, 'device_profile_get_by_id',
                               autospec=True) as mock_device_profile_get:
            mock_device_profile_get.return_value = self.fake_device_profile
            device_profile = objects.DeviceProfile.get_by_id(self.context, id)
            mock_device_profile_get.assert_called_once_with(self.context, id)
            self.assertEqual(self.context, device_profile._context)

    def test_list(self):
        with mock.patch.object(self.dbapi, 'device_profile_list',
                               autospec=True) as mock_device_profile_list:
            mock_device_profile_list.return_value = [self.fake_device_profile]
            device_profiles = objects.DeviceProfile.list(self.context)
            self.assertEqual(1, mock_device_profile_list.call_count)
            self.assertEqual(1, len(device_profiles))
            self.assertIsInstance(device_profiles[0], objects.DeviceProfile)
            self.assertEqual(self.context, device_profiles[0]._context)

    def test_create(self):
        with mock.patch.object(self.dbapi, 'device_profile_create',
                               autospec=True) as mock_device_profile_create:
            mock_device_profile_create.return_value = self.fake_device_profile
            device_profile = objects.DeviceProfile(self.context,
                                                   **self.fake_device_profile)
            device_profile.create(self.context)
            mock_device_profile_create.assert_called_once_with(
                self.context, self.fake_device_profile)
            self.assertEqual(self.context, device_profile._context)

    def test_destroy(self):
        uuid = self.fake_device_profile['uuid']
        with mock.patch.object(self.dbapi, 'device_profile_get_by_uuid',
                               autospec=True) as mock_device_profile_get:
            mock_device_profile_get.return_value = self.fake_device_profile
            with mock.patch.object(self.dbapi, 'device_profile_delete',
                                   autospec=True) as m_device_profile_delete:
                device_profile = objects.DeviceProfile.get(self.context, uuid)
                device_profile.destroy(self.context)
                m_device_profile_delete.assert_called_once_with(
                    self.context, uuid)
                self.assertEqual(self.context, device_profile._context)

    def test_update(self):
        uuid = self.fake_device_profile['uuid']
        with mock.patch.object(self.dbapi, 'device_profile_get_by_uuid',
                               autospec=True) as mock_device_profile_get:
            mock_device_profile_get.return_value = self.fake_device_profile
            with mock.patch.object(self.dbapi, 'device_profile_update',
                                   autospec=True) as m_device_profile_update:
                fake = self.fake_device_profile
                fake["profile_json"] = '{"version": 2.0,}'
                m_device_profile_update.return_value = fake
                dev_prof = objects.DeviceProfile.get(self.context, uuid)
                dev_prof.profile_json = '{"version": 2.0,}'
                dev_prof.save(self.context)
                mock_device_profile_get.assert_called_once_with(self.context,
                                                                uuid)
                m_device_profile_update.assert_called_once_with(
                    self.context, uuid,
                    {'profile_json': '{"version": 2.0,}'})
                self.assertEqual(self.context, dev_prof._context)
