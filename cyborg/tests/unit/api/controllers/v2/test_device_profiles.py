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

from six.moves import http_client
from unittest import mock

from oslo_serialization import jsonutils

from cyborg.tests.unit.api.controllers.v2 import base as v2_test
from cyborg.tests.unit import fake_device_profile


class TestDeviceProfileController(v2_test.APITestV2):
    DP_URL = '/device_profiles'

    def setUp(self):
        super(TestDeviceProfileController, self).setUp()
        self.headers = self.gen_headers(self.context)
        self.fake_dp_objs = fake_device_profile.get_obj_devprofs()
        self.fake_dps = fake_device_profile.get_api_devprofs()

    def _validate_links(self, links, dp_uuid):
        has_self_link = False
        for link in links:
            if link['rel'] == 'self':
                has_self_link = True
                url = link['href']
                components = url.split('/')
                self.assertEqual(components[-1], dp_uuid)
        self.assertTrue(has_self_link)

    def _validate_dp(self, in_dp, out_dp):
        self.assertEqual(in_dp['name'], out_dp['name'])
        self.assertEqual(in_dp['uuid'], out_dp['uuid'])
        self.assertEqual(in_dp['groups'], out_dp['groups'])

        # Check that the link is properly set up
        self._validate_links(out_dp['links'], in_dp['uuid'])

    @mock.patch('cyborg.objects.DeviceProfile.list')
    def test_get_one_by_uuid(self, mock_dp):
        dp = self.fake_dp_objs[0]
        mock_dp.return_value = [dp]
        url = self.DP_URL + '/%s'
        data = self.get_json(url % dp['uuid'], headers=self.headers)
        mock_dp.assert_called_once()
        out_dp = data['device_profile']
        self._validate_dp(dp, out_dp)

    @mock.patch('cyborg.objects.DeviceProfile.list')
    def test_get_all(self, mock_dp):
        mock_dp.return_value = self.fake_dp_objs
        data = self.get_json(self.DP_URL, headers=self.headers)
        out_dps = data['device_profiles']

        result = isinstance(out_dps, list)
        self.assertTrue(result)
        self.assertTrue(len(out_dps), len(self.fake_dp_objs))
        for in_dp, out_dp in zip(self.fake_dp_objs, out_dps):
            self._validate_dp(in_dp, out_dp)

    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.device_profile_create')
    def test_create(self, mock_cond_dp):
        dp = [self.fake_dps[0]]
        mock_cond_dp.return_value = self.fake_dp_objs[0]
        dp[0]['created_at'] = str(dp[0]['created_at'])
        response = self.post_json(self.DP_URL, dp, headers=self.headers)
        out_dp = jsonutils.loads(response.controller_output)

        self.assertEqual(http_client.CREATED, response.status_int)
        self._validate_dp(dp[0], out_dp)

    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.device_profile_delete')
    @mock.patch('cyborg.objects.DeviceProfile.get_by_name')
    @mock.patch('cyborg.objects.DeviceProfile.get_by_uuid')
    def test_delete(self, mock_dp_uuid, mock_dp_name, mock_cond_del):
        # Delete by UUID
        url = self.DP_URL + "/5d2c0797-c3cd-4f4b-b0d0-2cc5e99ef66e"
        response = self.delete(url, headers=self.headers)
        self.assertEqual(http_client.NO_CONTENT, response.status_int)
        # Delete by name
        url = self.DP_URL + "/mydp"
        response = self.delete(url, headers=self.headers)
        self.assertEqual(http_client.NO_CONTENT, response.status_int)
