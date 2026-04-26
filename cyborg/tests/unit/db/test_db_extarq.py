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

"""Tests for manipulating ExtArq via the DB API"""

from oslo_utils.fixture import uuidsentinel
from oslo_utils import uuidutils

from cyborg.common import exception
from cyborg.tests.unit.db import base
from cyborg.tests.unit.db import utils


class TestDbExtArq(base.DbTestCase):

    def test_create(self):
        random_uuid = uuidutils.generate_uuid()
        kw = {'uuid': random_uuid}
        created_extarq = utils.create_test_extarq(self.context, **kw)
        self.assertEqual(random_uuid, created_extarq['uuid'])

    def test_get_by_uuid(self):
        created_extarq = utils.create_test_extarq(self.context)
        queried_extarq = self.dbapi.extarq_get(
            self.context, created_extarq['uuid'])
        self.assertEqual(created_extarq['uuid'], queried_extarq['uuid'])

    def test_update(self):
        created_extarq = utils.create_test_extarq(self.context)
        queried_extarq = self.dbapi.extarq_update(
            self.context, created_extarq['uuid'], {'state': 'Initial'})
        self.assertEqual('Initial', queried_extarq['state'])

    def test_list(self):
        uuids = []
        for i in range(1, 4):
            extarq = utils.create_test_extarq(
                self.context,
                id=i,
                uuid=uuidutils.generate_uuid())
            uuids.append(extarq['uuid'])
        extarqs = self.dbapi.extarq_list(self.context)
        extarq_uuids = [item.uuid for item in extarqs]
        self.assertEqual(sorted(uuids), sorted(extarq_uuids))

    def test_delete(self):
        created_extarq = utils.create_test_extarq(self.context)
        return_value = self.dbapi.extarq_delete(
            self.context,
            created_extarq['uuid'])
        self.assertIsNone(return_value)

    def test_get_by_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(exception.ResourceNotFound,
                          self.dbapi.extarq_get,
                          self.context, random_uuid)

    def test_delete_by_uuid_not_exist(self):
        random_uuid = uuidutils.generate_uuid()
        self.assertRaises(
            exception.ResourceNotFound,
            self.dbapi.extarq_delete,
            self.context,
            random_uuid,
        )

    def test_get_by_uuid_with_matching_project_id(self):
        pid = str(uuidsentinel.project_a)
        created = utils.create_test_extarq(self.context, project_id=pid)
        result = self.dbapi.extarq_get(
            self.context, created['uuid'], project_id=pid
        )
        self.assertEqual(created['uuid'], result['uuid'])

    def test_get_by_uuid_with_wrong_project_id(self):
        pid = str(uuidsentinel.project_a)
        other = str(uuidsentinel.project_b)
        created = utils.create_test_extarq(self.context, project_id=pid)
        self.assertRaises(
            exception.ResourceNotFound,
            self.dbapi.extarq_get,
            self.context,
            created['uuid'],
            project_id=other,
        )

    def test_get_by_uuid_no_project_filter_returns_any(self):
        pid = str(uuidsentinel.project_a)
        created = utils.create_test_extarq(self.context, project_id=pid)
        result = self.dbapi.extarq_get(self.context, created['uuid'])
        self.assertEqual(created['uuid'], result['uuid'])

    def test_delete_with_matching_project_id(self):
        pid = str(uuidsentinel.project_a)
        created = utils.create_test_extarq(self.context, project_id=pid)
        self.dbapi.extarq_delete(self.context, created['uuid'], project_id=pid)
        self.assertRaises(
            exception.ResourceNotFound,
            self.dbapi.extarq_get,
            self.context,
            created['uuid'],
        )

    def test_delete_with_wrong_project_id(self):
        pid = str(uuidsentinel.project_a)
        other = str(uuidsentinel.project_b)
        created = utils.create_test_extarq(self.context, project_id=pid)
        self.assertRaises(
            exception.ResourceNotFound,
            self.dbapi.extarq_delete,
            self.context,
            created['uuid'],
            project_id=other,
        )

    def test_list_with_project_id_filter(self):
        pid_a = str(uuidsentinel.project_a)
        pid_b = str(uuidsentinel.project_b)
        arq_a = utils.create_test_extarq(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid(),
            project_id=pid_a,
        )
        utils.create_test_extarq(
            self.context,
            id=2,
            uuid=uuidutils.generate_uuid(),
            project_id=pid_b,
        )
        results = self.dbapi.extarq_list(self.context, project_id=pid_a)
        result_uuids = [r.uuid for r in results]
        self.assertEqual([arq_a['uuid']], result_uuids)

    def test_list_without_project_id_filter_returns_all(self):
        pid_a = str(uuidsentinel.project_a)
        pid_b = str(uuidsentinel.project_b)
        utils.create_test_extarq(
            self.context,
            id=1,
            uuid=uuidutils.generate_uuid(),
            project_id=pid_a,
        )
        utils.create_test_extarq(
            self.context,
            id=2,
            uuid=uuidutils.generate_uuid(),
            project_id=pid_b,
        )
        results = self.dbapi.extarq_list(self.context)
        self.assertEqual(2, len(results))
