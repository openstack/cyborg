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

"""Tests for manipulating Device via the DB API"""

import sys

from oslo_utils import uuidutils

from cyborg.common import exception
from cyborg.tests.unit.db import base
from cyborg.tests.unit.db import utils


class TestDbDevice(base.DbTestCase):

    def test_create(self):
        random_uuid = uuidutils.generate_uuid()
        kw = {'uuid': random_uuid}
        created_device = utils.create_test_device(self.context, **kw)
        self.assertEqual(random_uuid, created_device['uuid'])

    def test_get_by_uuid(self):
        created_dev = utils.create_test_device(self.context)
        queried_dev = self.dbapi.device_get(
            self.context, created_dev['uuid'])
        self.assertEqual(created_dev['uuid'], queried_dev['uuid'])

    def test_get_by_id(self):
        created_dev = utils.create_test_device(self.context)
        queried_dev = self.dbapi.device_get_by_id(
            self.context, created_dev['id'])
        self.assertEqual(created_dev['id'], queried_dev['id'])

    def test_update(self):
        created_dev = utils.create_test_device(self.context)
        queried_dev = self.dbapi.device_update(
            self.context, created_dev['uuid'], {'hostname': 'myhost'})
        self.assertEqual('myhost', queried_dev['hostname'])

    def test_list(self):
        uuids = []
        for i in range(1, 4):
            dev = utils.create_test_device(
                self.context,
                id=i,
                uuid=uuidutils.generate_uuid())
            uuids.append(dev['uuid'])
        devs = self.dbapi.device_list(self.context)
        dev_uuids = [item.uuid for item in devs]
        self.assertEqual(sorted(uuids), sorted(dev_uuids))

    def test_list_by_filters(self):
        dev1 = utils.create_test_device(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid(),
            hostname='myhost1')
        utils.create_test_device(
            self.context,
            id=2,
            uuid=uuidutils.generate_uuid(),
            hostname='myhost2')
        res = self.dbapi.device_list_by_filters(
            self.context, filters={"hostname": "myhost1"})
        self.assertEqual(1, len(res))
        self.assertEqual(dev1['hostname'], res[0]['hostname'])

    def test_delete(self):
        created_dev = utils.create_test_device(self.context)
        return_value = self.dbapi.device_delete(
            self.context,
            created_dev['uuid'])
        self.assertIsNone(return_value)

    def test_list_filter_is_none(self):
        """The main test is filters=None. If filters=None,
        it will be initialized to {}, that will return all device
        same as the List Device API response.
        """
        dev1 = utils.create_test_device(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid())
        res = self.dbapi.device_list_by_filters(
            self.context, filters=None)
        self.assertEqual(1, len(res))
        self.assertEqual(dev1['uuid'], res[0]['uuid'])

    def test_get_by_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.device_get,
                          self.context, random_uuid)

    def test_get_by_id_not_exist(self):
        fake_id = sys.maxsize
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.device_get_by_id,
                          self.context, fake_id)

    def test_delete_by_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.device_delete,
                          self.context, random_uuid)
