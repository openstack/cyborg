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

import datetime
import mock
from oslo_utils import timeutils
from six.moves import http_client

from cyborg.conductor import rpcapi
from cyborg.tests.unit.api.controllers.v1 import base as v1_test
from cyborg.tests.unit.db import utils as db_utils
from cyborg.tests.unit.objects import utils as obj_utils


def gen_post_body(**kw):
    return db_utils.get_test_accelerator(**kw)


def _rpcapi_accelerator_create(context, obj_acc):
    """Fake used to mock out the conductor RPCAPI's accelerator_create method.

    Performs creation of the accelerator object and returns the created
    accelerator as-per the real method.
    """
    obj_acc.create(context)
    return obj_acc


class TestPost(v1_test.APITestV1):

    ACCELERATOR_UUID = '10efe63d-dfea-4a37-ad94-4116fba50981'

    def setUp(self):
        super(TestPost, self).setUp()
        self.headers = self.gen_headers(self.context)

        p = mock.patch.object(rpcapi.ConductorAPI, 'accelerator_create')
        self.mock_create = p.start()
        self.mock_create.side_effect = _rpcapi_accelerator_create
        self.addCleanup(p.stop)

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    def test_post(self, mock_uuid):
        mock_uuid.return_value = self.ACCELERATOR_UUID

        body = gen_post_body(name='post_accelerator')
        response = self.post_json('/accelerators', body, headers=self.headers)
        self.assertEqual(http_client.CREATED, response.status_int)
        response = response.json
        self.assertEqual(self.ACCELERATOR_UUID, response['uuid'])
        self.assertEqual(body['name'], response['name'])
        self.mock_create.assert_called_once_with(mock.ANY, mock.ANY)


class TestList(v1_test.APITestV1):

    def setUp(self):
        super(TestList, self).setUp()
        self.accs = []
        for i in range(3):
            acc = obj_utils.create_test_accelerator(self.context)
            self.accs.append(acc)
        self.acc = self.accs[0]
        self.context.tenant = self.acc.project_id
        self.headers = self.gen_headers(self.context)

    def test_get_one(self):
        data = self.get_json('/accelerators/%s' % self.acc.uuid,
                             headers=self.headers)
        self.assertEqual(self.acc.uuid, data['uuid'])
        self.assertIn('acc_capability', data)
        self.assertIn('acc_type', data)
        self.assertIn('created_at', data)
        self.assertIn('description', data)
        self.assertIn('device_type', data)
        self.assertIn('links', data)
        self.assertIn('name', data)
        self.assertIn('product_id', data)
        self.assertIn('project_id', data)
        self.assertIn('remotable', data)
        self.assertIn('updated_at', data)
        self.assertIn('user_id', data)
        self.assertIn('vendor_id', data)

    def test_get_all(self):
        data = self.get_json('/accelerators', headers=self.headers)
        self.assertEqual(3, len(data['accelerators']))
        data_uuids = [d['uuid'] for d in data['accelerators']]
        acc_uuids = [acc.uuid for acc in self.accs]
        self.assertItemsEqual(acc_uuids, data_uuids)


def _rpcapi_accelerator_update(context, obj_acc):
    """Fake used to mock out the conductor RPCAPI's accelerator_update method.

    Performs update of the accelerator object and returns the updated
    accelerator as-per the real method.
    """
    obj_acc.save(context)
    return obj_acc


class TestPatch(v1_test.APITestV1):

    def setUp(self):
        super(TestPatch, self).setUp()
        self.acc = obj_utils.create_test_accelerator(self.context)
        self.context.tenant = self.acc.project_id
        self.headers = self.gen_headers(self.context)

        p = mock.patch.object(rpcapi.ConductorAPI, 'accelerator_update')
        self.mock_update = p.start()
        self.mock_update.side_effect = _rpcapi_accelerator_update
        self.addCleanup(p.stop)

    @mock.patch.object(timeutils, 'utcnow')
    def test_patch(self, mock_utcnow):
        test_time = datetime.datetime(2012, 12, 12, 12, 12)
        mock_utcnow.return_value = test_time

        description = 'new-description'
        response = self.patch_json('/accelerators/%s' % self.acc.uuid,
                                   [{'path': '/description',
                                     'value': description,
                                     'op': 'replace'}],
                                   headers=self.headers)
        self.assertEqual(http_client.OK, response.status_code)
        data = self.get_json('/accelerators/%s' % self.acc.uuid,
                             headers=self.headers)
        self.assertEqual(description, data['description'])
        return_updated_at = timeutils.parse_isotime(
            data['updated_at']).replace(tzinfo=None)
        self.assertEqual(test_time, return_updated_at)
        self.mock_update.assert_called_once_with(mock.ANY, mock.ANY)


def _rpcapi_accelerator_delete(context, obj_acc):
    """Fake used to mock out the conductor RPCAPI's accelerator_delete method.

    Performs deletion of the accelerator object as-per the real method.
    """
    obj_acc.destroy(context)


class TestDelete(v1_test.APITestV1):

    def setUp(self):
        super(TestDelete, self).setUp()
        self.acc = obj_utils.create_test_accelerator(self.context)
        self.context.tenant = self.acc.project_id
        self.headers = self.gen_headers(self.context)

        p = mock.patch.object(rpcapi.ConductorAPI, 'accelerator_delete')
        self.mock_delete = p.start()
        self.mock_delete.side_effect = _rpcapi_accelerator_delete
        self.addCleanup(p.stop)

    def test_delete(self):
        response = self.delete('/accelerators/%s' % self.acc.uuid,
                               headers=self.headers)
        self.assertEqual(http_client.NO_CONTENT, response.status_code)
        self.mock_delete.assert_called_once_with(mock.ANY, mock.ANY)
