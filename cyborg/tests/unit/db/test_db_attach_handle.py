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

"""Tests for manipulating AttachHandle via the DB API"""

from oslo_utils import uuidutils

from cyborg.common import exception
from cyborg.tests.unit.db import base
from cyborg.tests.unit.db import utils


class TestDbAttachHandle(base.DbTestCase):

    def test_create(self):
        random_uuid = uuidutils.generate_uuid()
        kw = {'uuid': random_uuid}
        created_ah = utils.create_test_attach_handle(self.context, **kw)
        self.assertEqual(random_uuid, created_ah['uuid'])

    def test_get_by_uuid(self):
        created_ah = utils.create_test_attach_handle(self.context)
        queried_ah = self.dbapi.attach_handle_get_by_uuid(
            self.context, created_ah['uuid'])
        self.assertEqual(created_ah['uuid'], queried_ah['uuid'])

    def test_get_by_id(self):
        created_ah = utils.create_test_attach_handle(self.context)
        queried_ah = self.dbapi.attach_handle_get_by_id(
            self.context, created_ah['id'])
        self.assertEqual(created_ah['id'], queried_ah['id'])

    def test_update(self):
        created_ah = utils.create_test_attach_handle(self.context)
        queried_ah = self.dbapi.attach_handle_update(
            self.context, created_ah['uuid'], {'attach_type': 'TEST_PCI'})
        self.assertEqual('TEST_PCI', queried_ah['attach_type'])

    def test_list(self):
        uuids = []
        for i in range(1, 4):
            ah = utils.create_test_attach_handle(
                self.context,
                id=i,
                uuid=uuidutils.generate_uuid())
            uuids.append(ah['uuid'])
        ahs = self.dbapi.attach_handle_list(self.context)
        ah_uuids = [item.uuid for item in ahs]
        self.assertEqual(sorted(uuids), sorted(ah_uuids))

    def test_list_by_type(self):
        ah1 = utils.create_test_attach_handle(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid(),
            attach_type='PCI')
        utils.create_test_attach_handle(
            self.context,
            id=2,
            uuid=uuidutils.generate_uuid(),
            attach_type='TEST_PCI')
        res = self.dbapi.attach_handle_list_by_type(
            self.context, attach_type='PCI')
        self.assertEqual(1, len(res))
        self.assertEqual(ah1['uuid'], res[0]['uuid'])

    def test_get_by_filters(self):
        ah1 = utils.create_test_attach_handle(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid(),
            deployable_id=1)
        utils.create_test_attach_handle(
            self.context,
            id=2,
            uuid=uuidutils.generate_uuid(),
            deployable_id=2)
        res = self.dbapi.attach_handle_get_by_filters(
            self.context, filters={"deployable_id": 1})
        self.assertEqual(1, len(res))
        self.assertEqual(ah1['uuid'], res[0]['uuid'])

    def test_allocate(self):
        utils.create_test_attach_handle(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid(),
            deployable_id=1)
        allocate_ah = self.dbapi.attach_handle_allocate(
            self.context, deployable_id=1)
        self.assertTrue(allocate_ah['in_use'])

    def test_delete(self):
        created_ah = utils.create_test_attach_handle(self.context)
        return_value = self.dbapi.attach_handle_delete(
            self.context,
            created_ah['uuid'])
        self.assertIsNone(return_value)

    def test_list_filter_is_none(self):
        """The main test is filters=None. If filters=None,
        it will be initialized to {}, that will return all attach
        handle same as the List Attach Handle API response.
        """
        ah1 = utils.create_test_attach_handle(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid())
        res = self.dbapi.attach_handle_get_by_filters(
            self.context, filters=None)
        self.assertEqual(1, len(res))
        self.assertEqual(ah1['uuid'], res[0]['uuid'])

    def test_get_by_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.attach_handle_get_by_uuid,
                          self.context, random_uuid)

    def test_delete_by_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.attach_handle_delete,
                          self.context, random_uuid)

    def test_do_allocate_attach_handle(self):
        dep_id = 100
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi._do_allocate_attach_handle,
                          self.context, dep_id)
