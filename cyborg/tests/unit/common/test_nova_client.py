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
import copy
import fixtures
import mock

from cyborg.common import exception
from cyborg.common import nova_client
from cyborg.tests import base


class NovaAPITest(base.TestCase):
    wsgi_api_version = '2.81'  # TODO(Sundar): Make this 2.82

    def setUp(self):
        super(NovaAPITest, self).setUp()
        self.instance_uuid = '00000000-0000-0000-0000-000000000001'
        self.event = {'name': 'accelerator-requests-bound',
                      'tag': 'mydp',
                      'server_uuid': self.instance_uuid,
                      'status': 'completed'}
        self.mock_sdk = self.useFixture(fixtures.MockPatch(
            'cyborg.common.utils.get_sdk_adapter')).mock.return_value
        self.mock_log_info = self.useFixture(fixtures.MockPatch(
            'cyborg.common.nova_client.LOG.info')).mock

    def test_send_event(self):
        self.useFixture(fixtures.EnvironmentVariable('OS_LOG_CAPTURE', 'True'))
        self.mock_sdk.post.return_value = mock.Mock(status_code=200)

        nova = nova_client.NovaAPI()
        result, resp = nova._send_event(self.event)
        self.assertTrue(result)
        self.assertEqual(resp.status_code, 200)

        msg = 'Sucessfully sent event to Nova, event: %(event)s'
        self.mock_log_info.assert_called_once_with(msg, {'event': self.event})

    def test_send_event_422(self):
        # If Nova returns HTTP 207 with event code 422, ignore it.
        resp_event = copy.deepcopy(self.event)
        resp_event.update({'status': 'failed', 'code': 422})
        nova_resp = {'events': [resp_event]}
        mock_ret = mock.Mock(status_code=207)
        mock_ret.json.return_value = nova_resp
        self.mock_sdk.post.return_value = mock_ret

        nova = nova_client.NovaAPI()
        result, resp = nova._send_event(self.event)
        self.assertTrue(result)
        self.assertEqual(resp.status_code, 207)

        msg = ('Ignoring Nova notification error that the instance %s is not '
               'yet associated with a host.')
        self.mock_log_info.assert_called_once_with(msg, self.instance_uuid)

    def test_send_event_failure(self):
        # Nova is expected to return 200/207 but this is future-proofing.
        mock_ret = mock.Mock(status_code=400)
        mock_ret.json.return_value = {}  # Dummy response
        self.mock_sdk.post.return_value = mock_ret

        nova = nova_client.NovaAPI()
        result, resp = nova._send_event(self.event)
        self.assertFalse(result)
        self.assertEqual(resp.status_code, 400)

    @mock.patch('cyborg.common.nova_client.NovaAPI._get_acc_changed_event')
    @mock.patch('cyborg.common.nova_client.NovaAPI._send_event')
    def test_notify_bind(self, mock_send_event, mock_get_event):
        nova_resp_text = 'itemNotFound'  # Dummy
        mock_ret = mock.Mock(status_code=404, text=nova_resp_text)
        mock_send_event.return_value = False, mock_ret

        nova = nova_client.NovaAPI()
        self.assertRaises(exception.NovaAPIConnectFailure,
                          nova.notify_binding, mock.ANY, mock.ANY, mock.ANY)
