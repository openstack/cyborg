# Copyright 2017 Huawei Technologies Co.,LTD.
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


class TestFPGAProgramController(v1_test.APITestV1):

    def setUp(self):
        super(TestFPGAProgramController, self).setUp()
        self.headers = self.gen_headers(self.context)
        self.deployable_uuids = ['0acbf8d6-e02a-4394-aae3-57557d209498']

    @mock.patch('cyborg.objects.Deployable.get')
    def test_program(self, mock_get_dep):
        self.headers['X-Roles'] = 'admin'
        self.headers['Content-Type'] = 'application/json'
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(self.context,
                                                       uuid=dep_uuid)
        mock_get_dep.return_value = fake_dep
        body = [{"image_uuid": "9a17439a-85d0-4c53-a3d3-0f68a2eac896"}]
        response = self.\
            patch_json('/accelerators/deployables/%s/program' % dep_uuid,
                       [{'path': '/program', 'value': body,
                        'op': 'replace'}],
                       headers=self.headers)
        self.assertEqual(http_client.OK, response.status_code)
        data = response.json_body
        self.assertEqual(dep_uuid, data['uuid'])
