# Copyright 2019 Intel, Inc.
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
import unittest

from oslo_serialization import jsonutils

from cyborg.tests.unit.api.controllers.v2 import base as v2_test
from cyborg.tests.unit import fake_device_profile
from cyborg.tests.unit import fake_extarq


class TestARQsController(v2_test.APITestV2):

    ARQ_URL = '/accelerator_requests'

    def setUp(self):
        super(TestARQsController, self).setUp()
        self.headers = self.gen_headers(self.context)
        self.fake_extarqs = fake_extarq.get_fake_extarq_objs()

    def _validate_links(self, links, arq_uuid):
        has_self_link = False
        for link in links:
            if link['rel'] == 'self':
                has_self_link = True
                url = link['href']
                components = url.split('/')
                self.assertEqual(components[-1], arq_uuid)
        self.assertTrue(has_self_link)

    def _validate_arq(self, in_arq, out_arq):
        for field in in_arq.keys():
            if field != 'id':
                self.assertEqual(in_arq[field], out_arq[field])

        # Check that the link is properly set up
        self._validate_links(out_arq['links'], in_arq['uuid'])

    @mock.patch('cyborg.objects.ExtARQ.get')
    def test_get_one_by_uuid(self, mock_extarq):
        in_extarq = self.fake_extarqs[0]
        in_arq = in_extarq.arq
        mock_extarq.return_value = in_extarq
        uuid = in_arq['uuid']

        url = self.ARQ_URL + '/%s'
        out_arq = self.get_json(url % uuid, headers=self.headers)
        mock_extarq.assert_called_once()
        self._validate_arq(in_arq, out_arq)

    @mock.patch('cyborg.objects.ExtARQ.list')
    def test_get_all(self, mock_extarqs):
        mock_extarqs.return_value = self.fake_extarqs
        data = self.get_json(self.ARQ_URL, headers=self.headers)
        out_arqs = data['arqs']

        result = isinstance(out_arqs, list)
        self.assertTrue(result)
        self.assertTrue(len(out_arqs), len(self.fake_extarqs))
        for in_extarq, out_arq in zip(self.fake_extarqs, out_arqs):
            self._validate_arq(in_extarq.arq, out_arq)

    @mock.patch('cyborg.objects.DeviceProfile.get_by_name')
    @mock.patch('cyborg.objects.ExtARQ.create')
    def test_create(self, mock_obj_extarq, mock_obj_dp):
        dp_list = fake_device_profile.get_obj_devprofs()
        mock_obj_dp.return_value = dp = dp_list[0]
        mock_obj_extarq.side_effect = self.fake_extarqs
        params = {'device_profile_name': dp['name']}
        response = self.post_json(self.ARQ_URL, params, headers=self.headers)
        data = jsonutils.loads(response.__dict__['controller_output'])
        out_arqs = data['arqs']

        self.assertEqual(http_client.CREATED, response.status_int)
        self.assertEqual(len(out_arqs), 3)
        for in_extarq, out_arq in zip(self.fake_extarqs, out_arqs):
            self._validate_arq(in_extarq.arq, out_arq)
        for idx, out_arq in enumerate(out_arqs):
            dp_group_id = 1
            if idx == 0:  # 1st arq has group_id '0', other 2 have '1'
                dp_group_id = 0
            self.assertEqual(dp_group_id, out_arq['device_profile_group_id'])

    @mock.patch('cyborg.objects.ExtARQ.delete_by_uuid')
    @mock.patch('cyborg.objects.ExtARQ.delete_by_instance')
    def test_delete(self, mock_by_inst, mock_by_arq):
        url = self.ARQ_URL
        arq = self.fake_extarqs[0].arq
        instance = arq.instance_uuid

        mock_by_arq.return_value = None
        args = '?' + "arqs=" + str(arq['uuid'])
        response = self.delete(url + args, headers=self.headers)
        self.assertEqual(http_client.NO_CONTENT, response.status_int)

        mock_by_inst.return_value = None
        args = '?' + "instance=" + instance
        response = self.delete(url + args, headers=self.headers)
        self.assertEqual(http_client.NO_CONTENT, response.status_int)

    @unittest.skip("Need more code to implement _get_resource in rbac")
    def test_delete_with_non_default(self):
        value = {"is_admin": False, "roles": "user", "is_admin_project": False}
        ct = self.gen_context(value)
        headers = self.gen_headers(ct)
        url = self.ARQ_URL
        arq = self.fake_extarqs[0].arq
        args = '?' + "arqs=" + str(arq['uuid'])
        exc = None
        try:
            self.delete(url + args, headers=headers)
        except Exception as e:
            exc = e
        # Cyborg does not raise different exception when policy check failed
        # now, improve this case with assertRaises later.
        self.assertIn("Bad response: 403 Forbidden", exc.args[0])
