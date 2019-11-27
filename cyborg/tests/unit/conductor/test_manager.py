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
import mock

from cyborg.conductor import manager
from cyborg.tests import base


class ConductorManagerTest(base.TestCase):
    def setUp(self):
        super(ConductorManagerTest, self).setUp()
        self.placement_mock = self.useFixture(fixtures.MockPatch(
            'cyborg.common.placement_client.PlacementClient')
        ).mock.return_value
        self.cm = manager.ConductorManager(
            mock.sentinel.topic, mock.sentinel.host)

    def test__gen_resource_inventory(self):
        expected = {
            'CUSTOM_FOO': {
                'total': 42,
                'max_unit': 42,
            },
        }
        actual = manager._gen_resource_inventory('CUSTOM_FOO', 42)
        self.assertEqual(expected, actual)

    @mock.patch('cyborg.conductor.manager.ConductorManager._get_sub_provider')
    def test_provider_report(self, mock_get_sub):
        rc = 'CUSTOM_ACCELERATOR'
        traits = ["CUSTOM_FPGA_INTEL",
                  "CUSTOM_FPGA_INTEL_ARRIA10",
                  "CUSTOM_FPGA_INTEL_REGION_UUID",
                  "CUSTOM_FPGA_FUNCTION_ID_INTEL_UUID",
                  "CUSTOM_PROGRAMMABLE",
                  "CUSTOM_FPGA_NETWORK"]
        total = 42
        expected_inv = {
            rc: {
                'total': total,
                'max_unit': total,
            },
        }
        # Test this exception path, since it doesn't actually change the flow.
        # Use a random exception, because it doesn't matter.
        self.placement_mock.ensure_resource_classes.side_effect = ValueError(
            'fail')

        actual = self.cm.provider_report(
            mock.sentinel.context, mock.sentinel.name, rc, traits, total,
            mock.sentinel.parent)

        self.placement_mock.ensure_resource_classes.assert_called_once_with(
            mock.sentinel.context, [rc])
        mock_get_sub.assert_called_once_with(
            mock.sentinel.context, mock.sentinel.parent, mock.sentinel.name)
        sub_pr_uuid = mock_get_sub.return_value
        self.placement_mock.update_inventory.assert_called_once_with(
            sub_pr_uuid, expected_inv)
        self.placement_mock.add_traits_to_rp.assert_called_once_with(
            sub_pr_uuid, traits)
        self.assertEqual(sub_pr_uuid, actual)
