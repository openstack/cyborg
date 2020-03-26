# Copyright 2020 ZTE Corporation.
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

"""Tests for manipulating DeviceProfile via the DB API"""

import sys

from oslo_utils import uuidutils

from cyborg.common import exception
from cyborg.tests.unit.db import base
from cyborg.tests.unit.db import utils


class TestDbDeviceProfile(base.DbTestCase):

    def test_get_by_uuid(self):
        created_dp = utils.create_test_device_profile(self.context)
        queried_dp = self.dbapi.device_profile_get_by_uuid(
            self.context, created_dp['uuid'])
        self.assertEqual(created_dp['uuid'], queried_dp['uuid'])
        self.assertIn('description', queried_dp)

    def test_get_by_id(self):
        created_dp = utils.create_test_device_profile(self.context)
        queried_dp = self.dbapi.device_profile_get_by_id(
            self.context, created_dp['id'])
        self.assertEqual(created_dp['id'], queried_dp['id'])
        self.assertIn('description', queried_dp)

    def test_update_with_name(self):
        created_dp = utils.create_test_device_profile(self.context)
        queried_dp = self.dbapi.device_profile_update(
            self.context, created_dp['uuid'], {'name': 'updated_name'})
        self.assertEqual('updated_name', queried_dp['name'])

    def test_update_with_description(self):
        created_dp = utils.create_test_device_profile(self.context)
        queried_dp = self.dbapi.device_profile_update(
            self.context, created_dp['uuid'], {'description': 'fake-desc'})
        self.assertEqual('fake-desc', queried_dp['description'])

    def test_list(self):
        uuids = []
        for i in range(1, 4):
            dp = utils.create_test_device_profile(
                self.context,
                id=i,
                uuid=uuidutils.generate_uuid(),
                name="device_profile_name_%s" % i)
            uuids.append(dp['uuid'])
        dps = self.dbapi.device_profile_list(self.context)
        dp_uuids = [item.uuid for item in dps]
        self.assertEqual(sorted(uuids), sorted(dp_uuids))

    def test_list_filter_by_name(self):
        utils.create_test_device_profile(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid(),
            name="name_1")
        utils.create_test_device_profile(
            self.context,
            id=2,
            uuid=uuidutils.generate_uuid(),
            name="name_2")
        res = self.dbapi.device_profile_list_by_filters(
            self.context, filters={"name": "name_1"})
        self.assertEqual(1, len(res))
        self.assertEqual('name_1', res[0]['name'])

    def test_delete(self):
        created_dp = utils.create_test_device_profile(self.context)
        return_value = self.dbapi.device_profile_delete(
            self.context,
            created_dp['uuid'])
        self.assertIsNone(return_value)

    def test_get_by_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.device_profile_get_by_uuid,
                          self.context, random_uuid)

    def test_list_filter_is_none(self):
        """The main test is filters=None. If filters=None,
        it will be initialized to {}, that will return all device
        profiles same as the List Device Profiles API response.
        """
        utils.create_test_device_profile(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid(),
            name="foo_dp")
        res = self.dbapi.device_profile_list_by_filters(
            self.context, filters=None)
        self.assertEqual(1, len(res))
        self.assertEqual('foo_dp', res[0]['name'])

    def test_update_with_uuid_not_exist(self):
        utils.create_test_device_profile(self.context)
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.device_profile_update,
                          self.context,
                          random_uuid,
                          {'name': 'updated_name'})

    def test_get_by_id_not_exist(self):
        fake_id = sys.maxsize
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.device_profile_get_by_id,
                          self.context, fake_id)

    def test_get_by_name_not_exist(self):
        random_name = 'fake' + uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.device_profile_get,
                          self.context, random_name)

    def test_delete_by_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.device_profile_delete,
                          self.context, random_uuid)
