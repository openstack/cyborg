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
from unittest import mock

from cyborg.common import exception
from cyborg.common import nova_client
from cyborg.tests import base


class NovaAPITest(base.TestCase):
    wsgi_api_version = '2.81'  # TODO(Sundar): Make this 2.82

    def setUp(self):
        super(NovaAPITest, self).setUp()
        self.instance_uuid = '00000000-0000-0000-0000-000000000001'
        template = {'name': 'accelerator-request-bound',
                    'server_uuid': self.instance_uuid,
                    'code': 200,
                    'status': 'completed'}
        tags = ['00000000-0000-0000-0000-000000000002',
                '00000000-0000-0000-0000-000000000003']
        self.events = [dict(template, tag=tag) for tag in tags]

        self.mock_sdk = self.useFixture(fixtures.MockPatch(
            'cyborg.common.utils.get_sdk_adapter')).mock.return_value
        self.mock_log_info = self.useFixture(fixtures.MockPatch(
            'cyborg.common.nova_client.LOG.info')).mock

    def test_send_events(self):
        self.mock_sdk.post.return_value = mock.Mock(status_code=200)

        nova = nova_client.NovaAPI()
        nova._send_events(self.events)

        msg = 'Sucessfully sent events to Nova, events: %(events)s'
        self.mock_log_info.assert_called_once_with(
            msg, {'events': self.events})

    def test_send_events_422(self):
        # If Nova returns HTTP 207 with event code 422 for all events,
        # ignore it.
        resp_events = copy.deepcopy(self.events)
        for ev in resp_events:
            ev.update({'status': 'failed', 'code': 422})
        nova_resp = {'events': resp_events}
        mock_ret = mock.Mock(status_code=207)
        mock_ret.json.return_value = nova_resp
        self.mock_sdk.post.return_value = mock_ret

        nova = nova_client.NovaAPI()
        nova._send_events(self.events)

        msg = ('Ignoring Nova notification error that the instance %s is not '
               'yet associated with a host.')
        self.mock_log_info.assert_called_once_with(msg, self.instance_uuid)

    def test_send_events_422_exception(self):
        # If Nova returns HTTP 207 with event code 422 for some events,
        # but not all, raise an exception. This is not expected to
        # happen with current code.
        resp_events = copy.deepcopy(self.events)
        resp_events[0].update({'status': 'failed', 'code': 422})
        nova_resp = {'events': resp_events}
        mock_ret = mock.Mock(status_code=207)
        mock_ret.json.return_value = nova_resp
        self.mock_sdk.post.return_value = mock_ret

        nova = nova_client.NovaAPI()
        self.assertRaises(exception.InvalidAPIResponse,
                          nova._send_events, self.events)

    def test_send_events_non_422_exception(self):
        # If Nova returns HTTP 207 with event code other than 422,
        # raise an exception.
        resp_events = copy.deepcopy(self.events)
        resp_events[0].update({'status': 'failed', 'code': 400})
        nova_resp = {'events': resp_events}
        mock_ret = mock.Mock(status_code=207)
        mock_ret.json.return_value = nova_resp
        self.mock_sdk.post.return_value = mock_ret

        nova = nova_client.NovaAPI()
        self.assertRaises(exception.InvalidAPIResponse,
                          nova._send_events, self.events)

    def test_send_events_failure(self):
        # Nova is expected to return 200/207 but this is future-proofing.
        mock_ret = mock.Mock(status_code=400)
        mock_ret.json.return_value = {}  # Dummy response
        self.mock_sdk.post.return_value = mock_ret

        nova = nova_client.NovaAPI()
        self.assertRaises(exception.InvalidAPIResponse,
                          nova._send_events, self.events)
