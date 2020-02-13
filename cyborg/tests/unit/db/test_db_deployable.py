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

"""Tests for manipulating Deployable via the DB API"""

from oslo_utils import uuidutils

from cyborg.common import exception
from cyborg.tests.unit.db import base
from cyborg.tests.unit.db import utils


class TestDbDeployable(base.DbTestCase):

    def test_create(self):
        kw = {'name': 'test_create_dep'}
        created_dep = utils.create_test_deployable(self.context, **kw)
        self.assertEqual(created_dep['name'], kw['name'])

    def test_get_by_uuid(self):
        created_dep = utils.create_test_deployable(self.context)
        queried_dep = self.dbapi.deployable_get(
            self.context, created_dep['uuid'])
        self.assertEqual(created_dep['uuid'], queried_dep['uuid'])

    def test_get_by_rp_uuid(self):
        created_dep = utils.create_test_deployable(self.context)
        queried_dep = self.dbapi.deployable_get_by_rp_uuid(
            self.context, created_dep['rp_uuid'])
        self.assertEqual(created_dep['uuid'], queried_dep['uuid'])

    def test_update(self):
        created_dep = utils.create_test_deployable(self.context)
        bit_stream_id = '10efe63d-dfea-4a37-ad94-4116fba5011'
        queried_dep = self.dbapi.deployable_update(
            self.context, created_dep['uuid'],
            {'bit_stream_id': bit_stream_id})
        self.assertEqual(bit_stream_id, queried_dep['bit_stream_id'])

    def test_list(self):
        uuids = []
        for i in range(1, 4):
            dep = utils.create_test_deployable(
                self.context,
                id=i,
                uuid=uuidutils.generate_uuid())
            uuids.append(dep['uuid'])
        deps = self.dbapi.deployable_list(self.context)
        dep_uuids = [item.uuid for item in deps]
        self.assertEqual(sorted(uuids), sorted(dep_uuids))

    def test_delete(self):
        created_dep = utils.create_test_deployable(self.context)
        return_value = self.dbapi.deployable_delete(
            self.context,
            created_dep['uuid'])
        self.assertIsNone(return_value)

    def test_list_by_filters(self):
        dep1 = utils.create_test_deployable(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid(),
            name='mydep1')
        utils.create_test_deployable(
            self.context,
            id=2,
            uuid=uuidutils.generate_uuid(),
            name='mydep2')
        res = self.dbapi.deployable_get_by_filters(
            self.context, filters={"name": "mydep1"})
        self.assertEqual(1, len(res))
        self.assertEqual(dep1['name'], res[0]['name'])

    def test_list_filter_is_none(self):
        """The main test is filters=None. If filters=None,
        it will be initialized to {}, that will return all deployable
        same as the List Deployable API response.
        """
        dep1 = utils.create_test_deployable(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid())
        res = self.dbapi.deployable_get_by_filters(
            self.context, filters=None)
        self.assertEqual(1, len(res))
        self.assertEqual(dep1['uuid'], res[0]['uuid'])

    def test_get_by_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.deployable_get,
                          self.context, random_uuid)

    def test_get_by_rp_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.deployable_get_by_rp_uuid,
                          self.context, random_uuid)

    def test_delete_by_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.deployable_delete,
                          self.context, random_uuid)
