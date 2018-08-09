# Copyright 2018 Lenovo, Inc.
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

import mock
from six.moves import http_client

from cyborg.api.controllers.v1.deployables import Deployable
from cyborg.tests.unit.api.controllers.v1 import base as v1_test
from cyborg.tests.unit import fake_deployable
from cyborg.tests.unit.objects import utils as obj_utils


class TestDeployableController(v1_test.APITestV1):

    def setUp(self):
        super(TestDeployableController, self).setUp()
        self.headers = self.gen_headers(self.context)
        self.deployable_uuids = ['10efe63d-dfea-4a37-ad94-4116fba50981',
                                 '10efe63d-dfea-4a37-ad94-4116fba50982']

    @mock.patch('cyborg.objects.Deployable.get')
    def test_get_one(self, mock_get_dep):
        dep_uuid = self.deployable_uuids[0]
        mock_get_dep.return_value = fake_deployable.\
            fake_deployable_obj(self.context, uuid=dep_uuid)
        data = self.get_json('/accelerators/deployables/%s' % dep_uuid,
                             headers=self.headers)
        self.assertEqual(dep_uuid, data['uuid'])
        for attr in Deployable._wsme_attributes:
            self.assertIn(attr.name, data)
        mock_get_dep.assert_called_once_with(mock.ANY, dep_uuid)

    @mock.patch('cyborg.objects.Deployable.list')
    def test_get_all(self, mock_list_dep):
        fake_deps = []
        for uuid in self.deployable_uuids:
            fake_dep = fake_deployable.fake_deployable_obj(self.context,
                                                           uuid=uuid)
            fake_deps.append(fake_dep)
        mock_list_dep.return_value = fake_deps
        data = self.get_json('/accelerators/deployables',
                             headers=self.headers)
        self.assertEqual(len(self.deployable_uuids), len(data['deployables']))
        mock_list_dep.assert_called_once()

    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.deployable_update')
    @mock.patch('cyborg.objects.Deployable.get')
    def test_patch(self, mock_get_dep, mock_deployable_update):
        self.headers['X-Roles'] = 'admin'
        self.headers['Content-Type'] = 'application/json'
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(self.context,
                                                       uuid=dep_uuid)
        mock_get_dep.return_value = fake_dep
        instance_uuid = '10efe63d-dfea-4a37-ad94-4116fba50981'
        fake_dep.instance_uuid = instance_uuid
        mock_deployable_update.return_value = fake_dep
        response = self.patch_json('/accelerators/deployables/%s' % dep_uuid,
                                   [{'path': '/instance_uuid',
                                     'value': instance_uuid,
                                     'op': 'replace'}],
                                   headers=self.headers)
        self.assertEqual(http_client.OK, response.status_code)
        data = response.json_body
        self.assertEqual(instance_uuid, data['instance_uuid'])
        mock_deployable_update.assert_called_once()

    def test_get_all_with_sort(self):
        dps = []
        for uuid in self.deployable_uuids:
            dp = obj_utils.create_test_deployable(self.context,
                                                  uuid=uuid)
            dps.append(dp)
        data = self.get_json('/accelerators/deployables?'
                             'filters.field=sort_key&filters.value=created_at'
                             '&filters.field=sort_dir&filters.value=desc',
                             headers=self.headers)
        self.assertEqual(self.deployable_uuids[1],
                         data['deployables'][0]['uuid'])
        self.assertEqual(self.deployable_uuids[0],
                         data['deployables'][1]['uuid'])
