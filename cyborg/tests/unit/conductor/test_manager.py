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

from oslo_utils.fixture import uuidsentinel as uuids

from cyborg.common import exception
from cyborg.conductor import manager
from cyborg.tests import base
from cyborg.tests.unit import fake_driver_device


class ConductorManagerTest(base.TestCase):
    def setUp(self):
        super(ConductorManagerTest, self).setUp()
        self.placement_mock = self.useFixture(fixtures.MockPatch(
            'cyborg.common.placement_client.PlacementClient')
        ).mock.return_value
        self.cm = manager.ConductorManager(
            mock.sentinel.topic, mock.sentinel.host)
        self.fake_driver_devices = (fake_driver_device.
                                    get_fake_driver_devices_objs())
        self.fake_driver_depolyables = (fake_driver_device.
                                        get_fake_driver_deployable_objs())

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
        self.placement_mock.ensure_resource_classes.return_value = None
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

    def test_get_root_provider(self):
        self.placement_mock.get.return_value.json.return_value = {
            'resource_providers': [{'uuid': mock.sentinel.uuid}],
        }
        uuid = self.cm._get_root_provider(mock.sentinel.context, 'foo')
        self.assertEqual(mock.sentinel.uuid, uuid)

    def test_get_root_provider_not_found(self):
        self.placement_mock.get.return_value.json.return_value = {
            'resource_providers': [],
        }
        self.assertRaises(exception.PlacementResourceProviderNotFound,
                          self.cm._get_root_provider,
                          mock.sentinel.context, 'foo')

    def test_get_root_provider_unavailable(self):
        self.placement_mock.get.side_effect = exception.PlacementServerError(
            "Placement Server has some error at this time.")
        self.assertRaises(exception.PlacementServerError,
                          self.cm._get_root_provider,
                          mock.sentinel.context, 'foo')

    @mock.patch('cyborg.conductor.manager.ConductorManager.'
                '_delete_provider_and_sub_providers')
    @mock.patch('cyborg.conductor.manager.ConductorManager.'
                'get_placement_needed_info_and_report')
    @mock.patch('cyborg.objects.driver_objects.driver_device.'
                'DriverDevice.destroy')
    @mock.patch('cyborg.objects.driver_objects.driver_device.'
                'DriverDevice.create')
    def test_drv_device_make_diff(self, mock_create_driver_device,
                                  mock_destroy_driver_device,
                                  mock_placement_report,
                                  mock_placement_delete):
        old_driver_attr_list = []
        new_driver_attr_list = self.fake_driver_devices[:1]
        self.placement_mock.get.return_value.json.return_value = {
            'resource_providers': [{'uuid': mock.sentinel.uuid}],
        }

        mock_placement_report.side_effect = (
            exception.ResourceProviderCreationFailed(
                name=uuids.compute_node))

        self.cm.drv_device_make_diff(
            mock.sentinel.context, 'foo',
            old_driver_attr_list, new_driver_attr_list)

        mock_destroy_driver_device.assert_called_once()
        mock_placement_delete.assert_called_once()

    @mock.patch('cyborg.conductor.manager.ConductorManager.'
                '_delete_provider_and_sub_providers')
    @mock.patch('cyborg.conductor.manager.ConductorManager.'
                'get_placement_needed_info_and_report')
    @mock.patch('cyborg.objects.driver_objects.driver_deployable.'
                'DriverDeployable.destroy')
    @mock.patch('cyborg.objects.driver_objects.driver_deployable.'
                'DriverDeployable.create')
    def test_drv_deployable_make_diff(self, mock_create_driver_deployable,
                                      mock_destroy_driver_deployable,
                                      mock_placement_report,
                                      mock_placement_delete):
        old_driver_dep_list = []
        new_driver_dep_list = self.fake_driver_depolyables[:1]
        self.placement_mock.get.return_value.json.return_value = {
            'resource_providers': [{'uuid': mock.sentinel.uuid}],
        }

        mock_placement_report.side_effect = (
            exception.ResourceProviderCreationFailed(
                name=uuids.compute_node))

        self.cm.drv_deployable_make_diff(
            mock.sentinel.context, '1', '2',
            old_driver_dep_list, new_driver_dep_list, 'foo')

        mock_destroy_driver_deployable.assert_called_once()
        mock_placement_delete.assert_called_once()
