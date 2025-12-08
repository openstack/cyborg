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

import fixtures
from unittest import mock

from cyborg.common import service as cyborg_service
from cyborg.conf import CONF
from cyborg.tests import base


class TestRPCService(base.TestCase):

    def setUp(self):
        super(TestRPCService, self).setUp()
        self.topic = 'cyborg-conductor'
        self.host = 'test-host'
        self.manager_module = 'cyborg.conductor.manager'
        self.manager_class = 'ConductorManager'

        self.mock_try_import = self.useFixture(fixtures.MockPatch(
            'cyborg.common.service.importutils.try_import',
            autospec=True)).mock
        mock_module = mock.MagicMock()
        mock_manager_cls = mock.MagicMock()
        self.mock_manager = mock_manager_cls.return_value
        setattr(mock_module, self.manager_class, mock_manager_cls)
        self.mock_try_import.return_value = mock_module

        self.mock_get_server = self.useFixture(fixtures.MockPatch(
            'cyborg.common.service.rpc.get_server',
            autospec=True)).mock
        self.mock_rpcserver = self.mock_get_server.return_value

        self.mock_get_admin_context = self.useFixture(fixtures.MockPatch(
            'cyborg.common.service.context.get_admin_context',
            autospec=True)).mock
        self.mock_admin_context = (
            self.mock_get_admin_context.return_value)

        self.mock_log_info = self.useFixture(fixtures.MockPatch(
            'cyborg.common.service.LOG.info')).mock

    @mock.patch.object(
        cyborg_service.service.Service, 'start', autospec=True)
    def test_start(self, mock_super_start):
        svc = cyborg_service.RPCService(
            self.manager_module, self.manager_class,
            self.topic, host=self.host)
        svc.tg = mock.MagicMock()

        svc.start()

        mock_super_start.assert_called_once_with(svc)
        self.mock_get_server.assert_called_once()
        self.mock_rpcserver.start.assert_called_once()

        svc.tg.add_dynamic_timer_args.assert_called_once_with(
            self.mock_manager.periodic_tasks,
            kwargs={'context': self.mock_admin_context},
            periodic_interval_max=CONF.periodic_interval)

        self.mock_log_info.assert_called_once_with(
            'Created RPC server for service %(service)s on host '
            '%(host)s.',
            {'service': self.topic, 'host': self.host})
