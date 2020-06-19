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

from oslo_serialization import jsonutils


class TestControlpathIDObject(base.DbTestCase):

    def setUp(self):
        super(TestControlpathIDObject, self).setUp()
        self.fake_control_path = utils.get_test_control_path()

    def test_get(self):
        uuid = self.fake_control_path['uuid']
        with mock.patch.object(self.dbapi, 'control_path_get_by_uuid',
                               autospec=True) as mock_control_path_get:
            mock_control_path_get.return_value = self.fake_control_path
            control_path = objects.ControlpathID.get(self.context, uuid)
            mock_control_path_get.assert_called_once_with(self.context, uuid)
            self.assertEqual(self.context, control_path._context)

    def test_get_set_cpid_info_using_obj(self):
        uuid = self.fake_control_path['uuid']
        with mock.patch.object(self.dbapi, 'control_path_get_by_uuid',
                               autospec=True) as mock_control_path_get:
            mock_control_path_get.return_value = self.fake_control_path
            # test cpid_info_obj loader
            control_path = objects.ControlpathID.get(self.context, uuid)
            self.assertEqual(jsonutils.loads(control_path.cpid_info),
                             control_path.cpid_info_obj)
            # test cpid_info_obj setter
            control_path.cpid_info_obj = {'bus': "fake"}
            self.assertEqual(control_path.cpid_info,
                             jsonutils.dumps(control_path.cpid_info_obj))

    def test_list(self):
        with mock.patch.object(self.dbapi, 'control_path_list',
                               autospec=True) as mock_control_path_list:
            mock_control_path_list.return_value = [self.fake_control_path]
            control_paths = objects.ControlpathID.list(self.context)
            self.assertEqual(1, mock_control_path_list.call_count)
            self.assertEqual(1, len(control_paths))
            self.assertIsInstance(control_paths[0], objects.ControlpathID)
            self.assertEqual(self.context, control_paths[0]._context)

    def test_create(self):
        with mock.patch.object(self.dbapi, 'control_path_create',
                               autospec=True) as mock_control_path_create:
            mock_control_path_create.return_value = self.fake_control_path
            control_path = objects.ControlpathID(self.context,
                                                 **self.fake_control_path)
            control_path.create(self.context)
            mock_control_path_create.assert_called_once_with(
                self.context, self.fake_control_path)
            self.assertEqual(self.context, control_path._context)

    def test_destroy(self):
        uuid = self.fake_control_path['uuid']
        with mock.patch.object(self.dbapi, 'control_path_get_by_uuid',
                               autospec=True) as mock_control_path_get:
            mock_control_path_get.return_value = self.fake_control_path
            with mock.patch.object(self.dbapi, 'control_path_delete',
                                   autospec=True) as mock_control_path_delete:
                control_path = objects.ControlpathID.get(self.context, uuid)
                control_path.destroy(self.context)
                mock_control_path_delete.assert_called_once_with(self.context,
                                                                 uuid)
                self.assertEqual(self.context, control_path._context)

    def test_update(self):
        uuid = self.fake_control_path['uuid']
        with mock.patch.object(self.dbapi, 'control_path_get_by_uuid',
                               autospec=True) as mock_control_path_get:
            mock_control_path_get.return_value = self.fake_control_path
            with mock.patch.object(self.dbapi, 'control_path_update',
                                   autospec=True) as mock_control_path_update:
                fake = self.fake_control_path
                fake["cpid_info"] = "new_cpid_info"
                mock_control_path_update.return_value = fake
                control_path = objects.ControlpathID.get(self.context, uuid)
                control_path.cpid_info = 'new_cpid_info'
                control_path.save(self.context)
                mock_control_path_get.assert_called_once_with(self.context,
                                                              uuid)
                mock_control_path_update.assert_called_once_with(
                    self.context, uuid,
                    {'cpid_info': 'new_cpid_info'})
                self.assertEqual(self.context, control_path._context)
