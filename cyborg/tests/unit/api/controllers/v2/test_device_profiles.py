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

from http import HTTPStatus
from unittest import mock
import webtest

from oslo_serialization import jsonutils

from cyborg.api.controllers import base
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
        self.assertEqual(in_dp['description'], out_dp['description'])

        # Check that the link is properly set up
        self._validate_links(out_dp['links'], in_dp['uuid'])

    @mock.patch('cyborg.objects.DeviceProfile.get_by_uuid')
    def test_get_one_by_uuid(self, mock_dp_uuid):
        dp = self.fake_dp_objs[0]
        mock_dp_uuid.return_value = dp
        url = self.DP_URL + '/%s'
        data = self.get_json(url % dp['uuid'], headers=self.headers)
        mock_dp_uuid.assert_called_once()
        out_dp = data['device_profile']
        self._validate_dp(dp, out_dp)

    @mock.patch('cyborg.objects.DeviceProfile.get_by_name')
    def test_get_one_by_name_before_v22(self, mock_dp_name):
        dp = self.fake_dp_objs[0]
        mock_dp_name.return_value = dp
        url = self.DP_URL + '/%s'
        headers = self.headers
        headers[base.Version.current_api_version] = '2.1'
        self.assertRaisesRegex(
            webtest.app.AppError,
            "Request not acceptable.*",
            self.get_json,
            url % dp['name'],
            headers=headers)

    @mock.patch('cyborg.objects.DeviceProfile.get_by_name')
    def test_get_one_by_name(self, mock_dp_name):
        dp = self.fake_dp_objs[0]
        mock_dp_name.return_value = dp
        url = self.DP_URL + '/%s'
        headers = self.headers
        headers[base.Version.current_api_version] = '2.2'
        data = self.get_json(url % dp['name'],
                             headers=headers)
        mock_dp_name.assert_called_once()
        out_dp = data['device_profile']
        self._validate_dp(dp, out_dp)

    @mock.patch('cyborg.objects.DeviceProfile.list')
    def test_get_all(self, mock_dp):
        mock_dp.return_value = self.fake_dp_objs
        data = self.get_json(self.DP_URL, headers=self.headers)
        out_dps = data['device_profiles']

        result = isinstance(out_dps, list)
        self.assertTrue(result)
        self.assertEqual(len(out_dps), len(self.fake_dp_objs))
        for in_dp, out_dp in zip(self.fake_dp_objs, out_dps):
            self._validate_dp(in_dp, out_dp)

    @mock.patch('cyborg.objects.DeviceProfile.list')
    def test_get_all_by_name(self, mock_dp):
        mock_dp.return_value = self.fake_dp_objs
        name = 'dp_example_1'
        data = self.get_json(self.DP_URL + '?name=' + name,
                             headers=self.headers)
        out_dps = data['device_profiles']
        expected_dps = [dp for dp in self.fake_dp_objs if dp.name in [name]]

        result = isinstance(out_dps, list)
        self.assertTrue(result)
        self.assertEqual(len(out_dps), len(expected_dps))
        for in_dp, out_dp in zip(expected_dps, out_dps):
            self._validate_dp(in_dp, out_dp)

    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.device_profile_create')
    def test_create(self, mock_cond_dp):
        dp = [self.fake_dps[0]]
        mock_cond_dp.return_value = self.fake_dp_objs[0]
        dp[0]['created_at'] = str(dp[0]['created_at'])
        response = self.post_json(self.DP_URL, dp, headers=self.headers)
        out_dp = jsonutils.loads(response.controller_output)

        self.assertEqual(HTTPStatus.CREATED, response.status_int)
        self._validate_dp(dp[0], out_dp)

    def test_create_with_no_name(self):
        test_unsupported_dp = self.fake_dps[0]

        # delete dp name for test
        del test_unsupported_dp['name']
        test_unsupported_dp['created_at'] = str(
            test_unsupported_dp['created_at'])
        self.assertRaisesRegex(
            webtest.app.AppError,
            "DeviceProfile name needed.",
            self.post_json,
            self.DP_URL,
            [test_unsupported_dp],
            headers=self.headers)

    def test_create_with_unsupported_name(self):
        test_unsupported_dp = self.fake_dps[0]

        # generate special dp name for test
        test_unsupported_dp['name'] = '!'
        test_unsupported_dp['created_at'] = str(
            test_unsupported_dp['created_at'])
        self.assertRaisesRegex(
            webtest.app.AppError,
            ".*Device profile name must be of the form *",
            self.post_json,
            self.DP_URL,
            [test_unsupported_dp],
            headers=self.headers)

    def test_create_with_no_groups(self):
        test_unsupported_dp = self.fake_dps[0]

        # delete dp groups for test
        del test_unsupported_dp['groups']
        test_unsupported_dp['created_at'] = str(
            test_unsupported_dp['created_at'])
        self.assertRaisesRegex(
            webtest.app.AppError,
            "DeviceProfile needs groups field.",
            self.post_json,
            self.DP_URL,
            [test_unsupported_dp],
            headers=self.headers)

    def test_create_with_unsupported_group_key(self):
        test_unsupported_dp = self.fake_dps[0]

        # generate special dp group key for test
        del test_unsupported_dp['groups'][0]['resources:FPGA']
        test_unsupported_dp['groups'][0]['fake:FPGA'] = 'required'
        test_unsupported_dp['created_at'] = str(
            test_unsupported_dp['created_at'])
        self.assertRaisesRegex(
            webtest.app.AppError,
            ".*Device profile group keys must be of the form *",
            self.post_json,
            self.DP_URL,
            [test_unsupported_dp],
            headers=self.headers)

    def test_create_with_unsupported_trait_value(self):
        test_unsupported_dp = self.fake_dps[0]

        # generate special dp trait value for test
        test_unsupported_dp['groups'][0][
            'trait:CUSTOM_FPGA_INTEL_PAC_ARRIA10'] = 'fake'
        test_unsupported_dp['created_at'] = str(
            test_unsupported_dp['created_at'])
        self.assertRaisesRegex(
            webtest.app.AppError,
            ".*Unsupported trait value fake *",
            self.post_json,
            self.DP_URL,
            [test_unsupported_dp],
            headers=self.headers)

    def test_create_with_unsupported_trait_name(self):
        test_unsupported_dp = self.fake_dps[0]

        # generate special trait for test
        del test_unsupported_dp['groups'][0][
            'trait:CUSTOM_FPGA_INTEL_PAC_ARRIA10']
        test_unsupported_dp['groups'][0]['trait:FAKE_TRAIT'] = 'required'
        test_unsupported_dp['created_at'] = str(
            test_unsupported_dp['created_at'])
        self.assertRaisesRegex(
            webtest.app.AppError,
            ".*Unsupported trait name format FAKE_TRAIT.*",
            self.post_json,
            self.DP_URL,
            [test_unsupported_dp],
            headers=self.headers)

    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.device_profile_create')
    def test_create_with_extra_space_in_trait(self, mock_cond_dp):
        test_unsupported_dp = self.fake_dps[0]

        # generate a requested dp which has extra space in trait
        del test_unsupported_dp['groups'][0][
            'trait:CUSTOM_FPGA_INTEL_PAC_ARRIA10']
        test_unsupported_dp['groups'][0][
            'trait:  CUSTOM_FPGA_INTEL_PAC_ARRIA10'] = 'required'

        mock_cond_dp.return_value = self.fake_dp_objs[0]
        test_unsupported_dp['created_at'] = str(
            test_unsupported_dp['created_at'])

        response = self.post_json(
            self.DP_URL, [test_unsupported_dp], headers=self.headers)
        out_dp = jsonutils.loads(response.controller_output)

        # check that the extra space in trait:
        # {'trait:  CUSTOM_FPGA_INTEL_PAC_ARRIA10': 'required'} is
        # successful stripped by the _validate_post_request function, and
        # the created device_profile has no extra space in trait
        # {'trait:CUSTOM_FPGA_INTEL_PAC_ARRIA10': 'required}
        self.assertTrue(out_dp['groups'] == self.fake_dp_objs[0]['groups'])

    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.device_profile_create')
    def test_create_with_extra_space_in_rc(self, mock_cond_dp):
        test_unsupported_dp = self.fake_dps[0]

        # generate a requested dp which has extra space in rc
        del test_unsupported_dp['groups'][0]['resources:FPGA']
        test_unsupported_dp['groups'][0]['resources: FPGA '] = '1'

        mock_cond_dp.return_value = self.fake_dp_objs[0]
        test_unsupported_dp['created_at'] = str(
            test_unsupported_dp['created_at'])

        response = self.post_json(
            self.DP_URL, [test_unsupported_dp], headers=self.headers)
        out_dp = jsonutils.loads(response.controller_output)

        # check that the extra space in rc:{'resources: FPGA ': '1'} is
        # successful stripped by the _validate_post_request function, and
        # the created device_profile has no extra space in
        # rc:{'resources:FPGA': '1'}
        self.assertTrue(out_dp['groups'] == self.fake_dp_objs[0]['groups'])

    def test_create_with_unsupported_rc(self):
        test_unsupported_dp = self.fake_dps[0]
        # generate a special rc for test
        del test_unsupported_dp['groups'][0]['resources:FPGA']
        test_unsupported_dp['groups'][0]["resources:FAKE_RC"] = '1'

        test_unsupported_dp['created_at'] = str(
            test_unsupported_dp['created_at'])
        self.assertRaisesRegex(
            webtest.app.AppError,
            ".*Unsupported resource class FAKE_RC.*",
            self.post_json,
            self.DP_URL,
            [test_unsupported_dp],
            headers=self.headers)

    def test_create_with_invalid_resource_value(self):
        test_unsupported_dp = self.fake_dps[0]
        del test_unsupported_dp['groups'][0]['resources:FPGA']
        test_unsupported_dp['groups'][0]["resources:CUSTOM_FAKE_RC"] = 'fake'
        test_unsupported_dp['created_at'] = str(
            test_unsupported_dp['created_at'])
        self.assertRaisesRegex(
            webtest.app.AppError,
            ".*Resources number fake is invalid.*",
            self.post_json,
            self.DP_URL,
            [test_unsupported_dp],
            headers=self.headers)

    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.device_profile_delete')
    @mock.patch('cyborg.objects.DeviceProfile.get_by_name')
    @mock.patch('cyborg.objects.DeviceProfile.get_by_uuid')
    def test_delete(self, mock_dp_uuid, mock_dp_name, mock_cond_del):
        # Delete by UUID
        url = self.DP_URL + "/5d2c0797-c3cd-4f4b-b0d0-2cc5e99ef66e"
        response = self.delete(url, headers=self.headers)
        self.assertEqual(HTTPStatus.NO_CONTENT, response.status_int)
        # Delete by name
        url = self.DP_URL + "/mydp"
        response = self.delete(url, headers=self.headers)
        self.assertEqual(HTTPStatus.NO_CONTENT, response.status_int)
