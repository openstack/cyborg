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

from cyborg.conductor import rpcapi
from cyborg.tests.unit.api.controllers.v1 import base as v1_test
from cyborg.tests.unit.db import utils


def gen_post_body(**kw):
    return utils.get_test_accelerator(**kw)


def _rpcapi_accelerator_create(self, context, acc_obj):
    """Fake used to mock out the conductor RPCAPI's accelerator_create method.

    Performs creation of the accelerator object and returns the created
    accelerator as-per the real method.
    """
    acc_obj.create()
    return acc_obj


@mock.patch.object(rpcapi.ConductorAPI, 'accelerator_create', autospec=True,
                   side_effect=_rpcapi_accelerator_create)
class TestPost(v1_test.APITestV1):

    ACCELERATOR_UUID = '10efe63d-dfea-4a37-ad94-4116fba50981'

    def setUp(self):
        super(TestPost, self).setUp()

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    def test_accelerator_post(self, mock_uuid, mock_create):
        mock_uuid.return_value = self.ACCELERATOR_UUID

        body = gen_post_body(name='test_accelerator')
        headers = self.gen_headers(self.context)
        response = self.post_json('/accelerators', body, headers=headers)
        self.assertEqual(http_client.CREATED, response.status_int)
        response = response.json
        self.assertEqual(self.ACCELERATOR_UUID, response['uuid'])
        self.assertEqual(body['name'], response['name'])
        mock_create.assert_called_once_with(mock.ANY, mock.ANY, mock.ANY)
