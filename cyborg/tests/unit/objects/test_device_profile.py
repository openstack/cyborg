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
from cyborg.tests.unit.db import base
from cyborg.tests.unit.db import utils
from cyborg.tests.unit import fake_device_profile


class TestDeviceProfileObject(base.DbTestCase):

    def setUp(self):
        super(TestDeviceProfileObject, self).setUp()
        self.fake_device_profile = utils.get_test_device_profile()

    def test_get_by_name(self):
        name = self.fake_device_profile['name']
        with mock.patch.object(self.dbapi, 'device_profile_get',
                               autospec=True) as mock_db_devprof_get:
            mock_db_devprof_get.return_value = self.fake_device_profile
            obj_devprof = objects.DeviceProfile.get_by_name(self.context, name)
            mock_db_devprof_get.assert_called_once_with(self.context, name)
            self.assertEqual(self.context, obj_devprof._context)
            self.assertEqual(name, obj_devprof.name)
            self.assertIn('description', obj_devprof)

    def test_get_by_uuid(self):
        uuid = self.fake_device_profile['uuid']
        with mock.patch.object(self.dbapi, 'device_profile_get_by_uuid',
                               autospec=True) as mock_db_devprof_get:
            mock_db_devprof_get.return_value = self.fake_device_profile
            obj_devprof = objects.DeviceProfile.get_by_uuid(self.context, uuid)
            mock_db_devprof_get.assert_called_once_with(self.context, uuid)
            self.assertEqual(self.context, obj_devprof._context)
            self.assertEqual(uuid, obj_devprof.uuid)
            self.assertIn('description', obj_devprof)

    def test_list(self):
        with mock.patch.object(self.dbapi, 'device_profile_list',
                               autospec=True) as mock_db_devprof_list:
            mock_db_devprof_list.return_value = [self.fake_device_profile]
            obj_devprofs = objects.DeviceProfile.list(self.context)
            self.assertEqual(1, mock_db_devprof_list.call_count)
            self.assertEqual(1, len(obj_devprofs))
            self.assertIsInstance(obj_devprofs[0], objects.DeviceProfile)
            self.assertEqual(self.context, obj_devprofs[0]._context)
            self.assertEqual(self.fake_device_profile['name'],
                             obj_devprofs[0].name)
            self.assertEqual(self.fake_device_profile['description'],
                             obj_devprofs[0].description)

    def test_create(self):
        api_devprofs = fake_device_profile.get_api_devprofs()
        api_devprof = api_devprofs[0]
        db_devprofs = fake_device_profile.get_db_devprofs()
        db_devprof = db_devprofs[0]
        with mock.patch.object(self.dbapi, 'device_profile_create',
                               autospec=True) as mock_db_devprof_create:
            mock_db_devprof_create.return_value = self.fake_device_profile
            obj_devprof = objects.DeviceProfile(**api_devprof)
            obj_devprof.create(self.context)
            mock_db_devprof_create.assert_called_once_with(
                self.context, db_devprof)

    def test_destroy(self):
        uuid = self.fake_device_profile['uuid']
        with mock.patch.object(self.dbapi, 'device_profile_get_by_uuid',
                               autospec=True) as mock_dp_get:
            mock_dp_get.return_value = self.fake_device_profile
            with mock.patch.object(self.dbapi, 'device_profile_delete',
                                   autospec=True) as m_dp_delete:
                m_dp_delete.return_value = None
                obj_devprof = objects.DeviceProfile.get_by_uuid(
                    self.context, uuid)
                obj_devprof.destroy(self.context)
                m_dp_delete.assert_called_once_with(self.context, uuid)
                self.assertEqual(self.context, obj_devprof._context)

    def test_update(self):
        fake_db_devprofs = fake_device_profile.get_db_devprofs()
        fake_obj_devprofs = fake_device_profile.get_obj_devprofs()
        db_devprof = fake_db_devprofs[0]
        db_devprof['created_at'] = None
        db_devprof['updated_at'] = None
        with mock.patch.object(self.dbapi, 'device_profile_get_by_uuid',
                               autospec=True) as mock_dp_get:
            mock_dp_get.return_value = db_devprof
            uuid = fake_db_devprofs[0]['uuid']
            # Start with db_devprofs[0], corr. to fake_obj_devprofs[0]
            obj_devprof = objects.DeviceProfile.get_by_uuid(self.context, uuid)
            # Change contents to fake_obj_devprofs[1] except uuid
            obj_devprof = fake_obj_devprofs[1]
            obj_devprof['uuid'] = uuid
            with mock.patch.object(self.dbapi, 'device_profile_update',
                                   autospec=True) as mock_dp_update:
                mock_dp_update.return_value = db_devprof
                obj_devprof.save(self.context)
                mock_dp_get.assert_called_once_with(self.context, uuid)
                mock_dp_update.assert_called_once()

    def test_obj_make_compatible(self):
        dp_obj = objects.DeviceProfile(description="fake description")
        primitive = dp_obj.obj_to_primitive()
        dp_obj.obj_make_compatible(primitive['cyborg_object.data'], '1.0')
        self.assertNotIn('description', primitive['cyborg_object.data'])
        primitive = dp_obj.obj_to_primitive()
        dp_obj.obj_make_compatible(primitive['cyborg_object.data'], '1.1')
        self.assertIn('description', primitive['cyborg_object.data'])
