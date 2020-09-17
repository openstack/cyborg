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

"""Cyborg agent rpcapi test cases."""

import oslo_messaging as messaging

from cyborg.agent.rpcapi import AgentAPI
from cyborg.common import constants
from cyborg.common import rpc
from cyborg.objects import base as objects_base
from cyborg.tests import base
from oslo_context import context as oslo_context
from unittest import mock


class TestRPCAPI(base.TestCase):
    """Test agent rpcapi"""

    RPC_API_VERSION = '1.1'

    def setUp(self, topic=None):
        super(TestRPCAPI, self).setUp()
        self.topic = topic or constants.AGENT_TOPIC
        target = messaging.Target(topic=self.topic,
                                  version=self.RPC_API_VERSION)
        self.agent_rpcapi = AgentAPI()
        self.serializer = objects_base.CyborgObjectSerializer()
        self.client = rpc.get_client(target,
                                     version_cap=self.RPC_API_VERSION,
                                     serializer=self.serializer)

    def _test_rpc_call(self, method):
        ctxt = oslo_context.RequestContext(user_id='fake_user',
                                           project_id='fake_project')
        expect_val = True
        with mock.patch.object(self.agent_rpcapi,
                               'fpga_program') as mock_program:
            func_obj = getattr(self.agent_rpcapi, method)
            mock_program.return_value = expect_val
            actual_val = func_obj(ctxt, 'fake_dep_uuid')
            self.assertEqual(actual_val, expect_val)

    def test_fpga_program(self):
        self._test_rpc_call('fpga_program')
