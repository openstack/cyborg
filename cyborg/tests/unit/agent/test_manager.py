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

"""Cyborg agent manager test cases."""

import fixtures
from unittest import mock

from keystoneauth1 import exceptions as ks_exc

from cyborg.agent import manager
from cyborg.common import exception
from cyborg.tests import base


class TestAgentManager(base.TestCase):
    """Test Agent Manager resource provider name resolution."""

    def setUp(self):
        super(TestAgentManager, self).setUp()
        self.placement_mock = self.useFixture(fixtures.MockPatch(
            'cyborg.agent.manager.placement.PlacementClient')
        ).mock.return_value

    def _create_manager_with_mocks(self):
        """Create an AgentManager with all dependencies mocked."""
        with mock.patch('cyborg.agent.manager.FPGADriver'), \
                mock.patch('cyborg.agent.manager.cond_api.ConductorAPI'), \
                mock.patch('cyborg.agent.manager.AgentAPI'), \
                mock.patch('cyborg.agent.manager.ImageAPI'), \
                mock.patch('cyborg.agent.manager.ResourceTracker'):
            return manager.AgentManager('cyborg-agent-topic')

    @mock.patch('cyborg.agent.manager.CONF')
    def test_get_resource_provider_name_primary_success(self, mock_conf):
        """Test that primary hostname (FQDN) is used when RP exists."""
        mock_conf.agent.resource_provider_name = 'compute-0.example.com'
        mock_conf.agent.resource_provider_startup_retries = 0
        mock_conf.host = 'compute-0'

        # Primary hostname found in Placement
        self.placement_mock.get.return_value.json.return_value = {
            'resource_providers': [{'uuid': 'test-uuid'}]
        }

        am = self._create_manager_with_mocks()

        self.assertEqual('compute-0.example.com', am.resource_provider_name)
        # Should only call Placement once since primary succeeded
        self.assertEqual(1, self.placement_mock.get.call_count)

    @mock.patch('cyborg.agent.manager.CONF')
    def test_get_resource_provider_name_fallback_success(self, mock_conf):
        """Test fallback to CONF.host when primary hostname not found."""
        mock_conf.agent.resource_provider_name = 'compute-0.example.com'
        mock_conf.agent.resource_provider_startup_retries = 0
        mock_conf.host = 'compute-0'

        def get_side_effect(url):
            mock_response = mock.Mock()
            if 'compute-0.example.com' in url:
                # Primary hostname not found
                mock_response.json.return_value = {'resource_providers': []}
            else:
                # Fallback hostname found
                mock_response.json.return_value = {
                    'resource_providers': [{'uuid': 'test-uuid'}]
                }
            return mock_response

        self.placement_mock.get.side_effect = get_side_effect

        am = self._create_manager_with_mocks()

        self.assertEqual('compute-0', am.resource_provider_name)
        # Should have tried both primary and fallback
        self.assertEqual(2, self.placement_mock.get.call_count)

    @mock.patch('cyborg.agent.manager.CONF')
    def test_get_resource_provider_name_both_fail(self, mock_conf):
        """Test that exception is raised when neither hostname works."""
        mock_conf.agent.resource_provider_name = 'compute-0.example.com'
        mock_conf.agent.resource_provider_startup_retries = 0
        mock_conf.host = 'compute-0'

        # Neither hostname found
        self.placement_mock.get.return_value.json.return_value = {
            'resource_providers': []
        }

        self.assertRaises(
            exception.PlacementResourceProviderNotFound,
            self._create_manager_with_mocks)

    @mock.patch('cyborg.agent.manager.CONF')
    def test_get_resource_provider_name_config_override(self, mock_conf):
        """Test that configured resource_provider_name is used."""
        mock_conf.agent.resource_provider_name = 'custom-hostname'
        mock_conf.agent.resource_provider_startup_retries = 0
        mock_conf.host = 'compute-0'

        # Configured hostname found
        self.placement_mock.get.return_value.json.return_value = {
            'resource_providers': [{'uuid': 'test-uuid'}]
        }

        am = self._create_manager_with_mocks()

        self.assertEqual('custom-hostname', am.resource_provider_name)
        # Should use the configured name, not FQDN
        self.placement_mock.get.assert_called_once()
        call_url = self.placement_mock.get.call_args[0][0]
        self.assertIn('custom-hostname', call_url)

    @mock.patch('cyborg.agent.manager.CONF')
    def test_get_resource_provider_name_no_fallback_when_same(self, mock_conf):
        """Test no fallback when CONF.host equals primary hostname."""
        mock_conf.agent.resource_provider_name = 'compute-0'
        mock_conf.agent.resource_provider_startup_retries = 0
        mock_conf.host = 'compute-0'

        # Primary hostname not found, and no fallback to try
        self.placement_mock.get.return_value.json.return_value = {
            'resource_providers': []
        }

        self.assertRaises(
            exception.PlacementResourceProviderNotFound,
            self._create_manager_with_mocks)

        # Should only try once since hostname == CONF.host
        self.assertEqual(1, self.placement_mock.get.call_count)

    @mock.patch('cyborg.agent.manager.time')
    @mock.patch('cyborg.agent.manager.CONF')
    def test_get_resource_provider_name_retry_succeeds(
            self, mock_conf, mock_time):
        """Test retry succeeds on second attempt."""
        mock_conf.agent.resource_provider_name = 'compute-0.example.com'
        mock_conf.host = 'compute-0'
        mock_conf.agent.resource_provider_startup_retries = 3

        # First call: no providers; second call: found
        self.placement_mock.get.return_value.json.side_effect = [
            {'resource_providers': []},  # primary fail
            {'resource_providers': []},  # fallback fail
            {'resource_providers': [{'uuid': 'test-uuid'}]},  # primary ok
        ]

        am = self._create_manager_with_mocks()

        self.assertEqual('compute-0.example.com', am.resource_provider_name)
        mock_time.sleep.assert_called_once_with(1)

    @mock.patch('cyborg.agent.manager.time')
    @mock.patch('cyborg.agent.manager.CONF')
    def test_get_resource_provider_name_retry_exhausted(
            self, mock_conf, mock_time):
        """Test all retry attempts exhausted raises exception."""
        mock_conf.agent.resource_provider_name = 'compute-0.example.com'
        mock_conf.host = 'compute-0'
        mock_conf.agent.resource_provider_startup_retries = 2

        # All calls return no providers
        self.placement_mock.get.return_value.json.return_value = {
            'resource_providers': []
        }

        self.assertRaises(
            exception.PlacementResourceProviderNotFound,
            self._create_manager_with_mocks)

        # 3 total attempts (initial + 2 retries), sleep between each
        self.assertEqual(
            [mock.call(1), mock.call(2)],
            mock_time.sleep.call_args_list)

    @mock.patch('cyborg.agent.manager.time')
    @mock.patch('cyborg.agent.manager.CONF')
    def test_get_resource_provider_name_no_retry_when_zero(
            self, mock_conf, mock_time):
        """Test immediate failure when retries set to 0."""
        mock_conf.agent.resource_provider_name = 'compute-0.example.com'
        mock_conf.host = 'compute-0'
        mock_conf.agent.resource_provider_startup_retries = 0

        self.placement_mock.get.return_value.json.return_value = {
            'resource_providers': []
        }

        self.assertRaises(
            exception.PlacementResourceProviderNotFound,
            self._create_manager_with_mocks)

        mock_time.sleep.assert_not_called()

    @mock.patch('cyborg.agent.manager.CONF')
    def test_check_resource_provider_exists_placement_error(self, mock_conf):
        """Test that Placement errors cause startup failure."""
        mock_conf.agent.resource_provider_name = 'compute-0.example.com'
        mock_conf.agent.resource_provider_startup_retries = 0
        mock_conf.host = 'compute-0'

        # Placement raises an exception for all requests
        self.placement_mock.get.side_effect = ks_exc.ConnectFailure(
            'Placement unavailable')

        self.assertRaises(
            exception.PlacementResourceProviderNotFound,
            self._create_manager_with_mocks)
