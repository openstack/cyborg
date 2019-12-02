# Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from cyborg.api.controllers.v2 import versions
from cyborg.tests.unit.api import base as api_base


SERVICE_TYPE = 'accelerator'
H_MIN_VER = 'openstack-api-minimum-version'
H_MAX_VER = 'openstack-api-maximum-version'
H_RESP_VER = 'openstack-api-version'
MIN_VER = versions.min_version_string()
MAX_VER = versions.max_version_string()


class TestMicroversions(api_base.BaseApiTest):

    controller_list_response = [
        'id', 'links', 'max_version', 'min_version', 'status']

    def setUp(self):
        super(TestMicroversions, self).setUp()

    def test_wrong_major_version(self):
        response = self.get_json(
            '/v2',
            headers={'OpenStack-API-Version': ' '.join([SERVICE_TYPE,
                                                        '10'])},
            expect_errors=True, return_json=False)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(406, response.status_int)
        expected_error_msg = ('Invalid value for'
                              ' OpenStack-API-Version header')
        self.assertTrue(response.json['error_message'])
        self.assertIn(expected_error_msg, response.json['error_message'])

    def test_without_specified_microversion(self):
        """If the header OpenStack-API-Version is absent in user's request,
        the default microversion is MIN_VER.
        """
        response = self.get_json('/v2', return_json=False)
        self.assertEqual(response.headers[H_MIN_VER], MIN_VER)
        self.assertEqual(response.headers[H_MAX_VER], MAX_VER)
        self.assertEqual(response.headers[H_RESP_VER], MIN_VER)
        self.assertTrue(all(x in response.json.keys() for x in
                            self.controller_list_response))

    def test_new_client_new_api(self):
        response = self.get_json(
            '/v2',
            headers={'OpenStack-API-Version': ' '.join([SERVICE_TYPE,
                                                        '2.0'])},
            return_json=False)
        self.assertEqual(response.headers[H_MIN_VER], MIN_VER)
        self.assertEqual(response.headers[H_MAX_VER], MAX_VER)
        self.assertEqual(response.headers[H_RESP_VER], '2.0')
        self.assertTrue(all(x in response.json.keys() for x in
                            self.controller_list_response))

    def test_latest_microversion(self):
        response = self.get_json(
            '/v2',
            headers={'OpenStack-API-Version': ' '.join([SERVICE_TYPE,
                                                        'latest'])},
            return_json=False)
        self.assertEqual(response.headers[H_MIN_VER], MIN_VER)
        self.assertEqual(response.headers[H_MAX_VER], MAX_VER)
        self.assertEqual(response.headers[H_RESP_VER], MAX_VER)
        self.assertTrue(all(x in response.json.keys() for x in
                            self.controller_list_response))

    def test_unsupported_version(self):
        unsupported_version = str(float(MAX_VER) + 0.1)
        response = self.get_json(
            '/v2',
            headers={'OpenStack-API-Version': ' '.join(
                [SERVICE_TYPE, unsupported_version])},
            expect_errors=True)
        self.assertEqual(406, response.status_int)
        self.assertEqual(response.headers[H_MIN_VER], MIN_VER)
        self.assertEqual(response.headers[H_MAX_VER], MAX_VER)
        expected_error_msg = ('Version %s was requested but the minor '
                              'version is not supported by this service. '
                              'The supported version range is' %
                              unsupported_version)
        self.assertTrue(response.json['error_message'])
        self.assertIn(expected_error_msg, response.json['error_message'])
