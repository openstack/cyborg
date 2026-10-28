# Copyright (c) 2018 Intel.
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

"""Cyborg agent resource_tracker test cases."""

import copy

from unittest import mock

from oslo_serialization import jsonutils

from cyborg import conf
from cyborg.accelerator.drivers import driver
from cyborg.accelerator.drivers import fake
from cyborg.accelerator.drivers.pci.pci import driver as pci_driver
from cyborg.agent import resource_tracker
from cyborg.common import constants
from cyborg.common import exception
from cyborg.conductor import rpcapi as cond_api
from cyborg.tests import base
from cyborg.tests.unit import fake_driver_device


CONF = conf.CONF


class TestResourceTracker(base.TestCase):
    """Test Agent ResourceTracker"""

    def setUp(self):
        super().setUp()
        self.host = CONF.host
        self.cond_api = cond_api.ConductorAPI()
        self.rt = resource_tracker.ResourceTracker(self.host, self.cond_api)

    def test_update_usage(self):
        """Update the resource usage and stats after a change in an
        instance
        """
        # FIXME(Shaohe Feng) need add testcase. How to check the fpgas
        # has stored into DB by conductor correctly?
        pass

    def test_driver_lookup_before_resource_update(self):
        fake_driver = self.rt.acc_drivers['fake_driver']
        # The first periodic report runs discovery and builds the
        # control path to driver ownership map.
        self.rt.discover_devices()
        controlpath = fake_driver.discover()[0].controlpath_id
        rpc_controlpath = {
            'cpid_type': controlpath.cpid_type,
            'cpid_info': jsonutils.loads(controlpath.cpid_info),
        }

        self.assertIs(
            fake_driver,
            self.rt.get_driver_for_controlpath(rpc_controlpath),
        )

    def test_lookup_does_not_rediscover_missing_controlpath(self):
        with mock.patch.object(
            self.rt.acc_drivers['fake_driver'], 'discover'
        ) as discover:
            self.assertRaises(
                exception.InvalidConfiguration,
                self.rt.get_driver_for_controlpath,
                {'cpid_type': 'PCI', 'cpid_info': {'bus': 'ff'}},
            )
        discover.assert_not_called()

    def test_each_device_controlpath_maps_to_its_driver(self):
        fake_driver = fake.FakeDriver()
        fpga = fake_driver.discover()[0]
        gpu = copy.deepcopy(fpga)
        gpu.type = constants.DEVICE_GPU
        gpu.controlpath_id.cpid_info = (
            '{"domain":"0000","bus":"0d","device":"00","function":"0"}'
        )
        pci_drv = pci_driver.PCIDriver()
        self.rt.acc_drivers = {'pci': pci_drv, 'fake': fake_driver}

        with (
            mock.patch.object(
                pci_drv, 'discover', return_value=[gpu], autospec=True
            ),
            mock.patch.object(
                self.rt.conductor_api, 'report_data', autospec=True
            ) as report,
        ):
            self.rt.update_usage(self.context)

        report.assert_called_once_with(self.context, self.host, mock.ANY)
        self.assertEqual(
            [constants.DEVICE_GPU, constants.DEVICE_FPGA],
            [device.type for device in report.call_args.args[2]],
        )
        gpu_controlpath = {
            'cpid_type': gpu.controlpath_id.cpid_type,
            'cpid_info': jsonutils.loads(gpu.controlpath_id.cpid_info),
        }
        fpga_controlpath = {
            'cpid_type': fpga.controlpath_id.cpid_type,
            'cpid_info': jsonutils.loads(fpga.controlpath_id.cpid_info),
        }
        self.assertIs(
            pci_drv, self.rt.get_driver_for_controlpath(gpu_controlpath)
        )
        self.assertIs(
            fake_driver, self.rt.get_driver_for_controlpath(fpga_controlpath)
        )

    def test_equivalent_json_member_order_maps_to_same_driver(self):
        fake_driver = fake.FakeDriver()
        device = fake_driver.discover()[0]
        device.controlpath_id.cpid_info = (
            '{"function":"0","device":"00","bus":"0c","domain":"0000"}'
        )
        with mock.patch.object(
            fake_driver, 'discover', return_value=[device], autospec=True
        ):
            self.rt.acc_drivers = {'fake': fake_driver}
            with mock.patch.object(
                self.rt.conductor_api, 'report_data', autospec=True
            ) as report:
                self.rt.update_usage(self.context)

        report.assert_called_once_with(self.context, self.host, [device])
        rpc_controlpath = {
            'cpid_type': 'PCI',
            'cpid_info': {
                'domain': '0000',
                'bus': '0c',
                'device': '00',
                'function': '0',
            },
        }
        self.assertIs(
            fake_driver,
            self.rt.get_driver_for_controlpath(rpc_controlpath),
        )

    def test_duplicate_controlpath_is_a_config_error(self):
        fake_driver = fake.FakeDriver()
        other_driver = fake.FakeDriver()
        self.rt.acc_drivers = {'fake': fake_driver}
        controlpath = fake_driver.discover()[0].controlpath_id
        rpc_controlpath = {
            'cpid_type': controlpath.cpid_type,
            'cpid_info': jsonutils.loads(controlpath.cpid_info),
        }

        with mock.patch.object(
            self.rt.conductor_api, 'report_data', autospec=True
        ) as report:
            self.rt.update_usage(self.context)
            self.assertIs(
                fake_driver,
                self.rt.get_driver_for_controlpath(rpc_controlpath),
            )
            report.reset_mock()

            self.rt.acc_drivers['other'] = other_driver
            exc = self.assertRaises(
                exception.InvalidConfiguration,
                self.rt.update_usage,
                self.context,
            )

        report.assert_not_called()
        self.assertIn('claimed by both', str(exc))
        self.assertRaises(
            exception.InvalidConfiguration,
            self.rt.get_driver_for_controlpath,
            rpc_controlpath,
        )

    def test_periodic_report_replaces_map_when_device_disappears(self):
        fake_driver = fake.FakeDriver()
        self.rt.acc_drivers = {'fake': fake_driver}
        with mock.patch.object(
            self.rt.conductor_api, 'report_data', autospec=True
        ):
            self.rt.update_usage(self.context)

        controlpath = fake_driver.discover()[0].controlpath_id
        rpc_controlpath = {
            'cpid_type': controlpath.cpid_type,
            'cpid_info': jsonutils.loads(controlpath.cpid_info),
        }
        self.assertIs(
            fake_driver, self.rt.get_driver_for_controlpath(rpc_controlpath)
        )

        with (
            mock.patch.object(
                fake_driver, 'discover', return_value=[], autospec=True
            ),
            mock.patch.object(
                self.rt.conductor_api, 'report_data', autospec=True
            ) as report,
        ):
            self.rt.update_usage(self.context)

        report.assert_called_once_with(self.context, self.host, [])
        self.assertRaises(
            exception.InvalidConfiguration,
            self.rt.get_driver_for_controlpath,
            rpc_controlpath,
        )

    def test_initialize_acc_drivers(self):
        enabled_drivers = ['intel_fpga_driver']
        self.rt._initialize_drivers(enabled_drivers=enabled_drivers)
        drivers = self.rt.acc_drivers
        self.assertEqual(len(drivers), len(enabled_drivers))

    def test_initialize_duplicate_enabled_driver(self):
        self.flags(
            enabled_drivers=['fake_driver', 'pci_driver', 'fake_driver'],
            group='agent',
        )
        with mock.patch(
            'cyborg.agent.resource_tracker.extension.ExtensionManager'
        ) as extensions:
            exc = self.assertRaises(
                exception.InvalidConfiguration,
                self.rt._initialize_drivers,
            )

        extensions.assert_not_called()
        self.assertIn('fake_driver', str(exc))
        self.assertIn('[agent] enabled_drivers', str(exc))

    def test_initialize_invalid_driver(self):
        enabled_drivers = ['invalid_driver']
        self.assertRaises(
            exception.InvalidDriver,
            self.rt._initialize_drivers,
            enabled_drivers,
        )

    @mock.patch(
        'cyborg.agent.resource_tracker.driver.DriverManager', autospec=True
    )
    @mock.patch('stevedore.extension.ExtensionManager', autospec=True)
    def test_initialize_drivers_does_not_call_init_host(
        self, mock_extension_manager, mock_driver_manager
    ):
        mock_extension_manager.return_value.names.return_value = [
            'nvme_driver'
        ]
        mock_driver = mock.Mock()
        mock_driver_manager.return_value.driver = mock_driver

        self.rt._initialize_drivers(enabled_drivers=['nvme_driver'])

        mock_driver.init_host.assert_not_called()

    @mock.patch('cyborg.agent.resource_tracker.LOG')
    def test_update_usage_failed_parent_provider(self, mock_log):
        with mock.patch.object(self.rt.conductor_api, 'report_data') as m:
            m.side_effect = exception.PlacementResourceProviderNotFound(
                resource_provider='foo'
            )
            self.rt.update_usage(self.context)
            m.assert_called_once_with(self.context, 'fake-mini', mock.ANY)
        mock_log.error.assert_called_once_with(
            'Unable to report usage: %s', m.side_effect
        )

    def test_init_drivers_calls_each(self):
        drv1 = mock.create_autospec(driver.GenericDriver, instance=True)
        drv2 = mock.create_autospec(driver.GenericDriver, instance=True)
        self.rt.acc_drivers = {'a': drv1, 'b': drv2}
        self.rt.init_drivers()
        drv1.init_host.assert_called_once()
        drv2.init_host.assert_called_once()

    def test_init_drivers_propagates_exception(self):
        drv = mock.create_autospec(driver.GenericDriver, instance=True)
        drv.init_host.side_effect = exception.InvalidConfiguration(
            reason='nvme-cli not found'
        )
        self.rt.acc_drivers = {'nvme': drv}
        self.assertRaises(
            exception.InvalidConfiguration,
            self.rt.init_drivers,
        )

    def test_init_host_rejects_duplicate_devices(self):
        drv1 = mock.create_autospec(driver.GenericDriver, instance=True)
        drv2 = mock.create_autospec(driver.GenericDriver, instance=True)
        drv1.discover.return_value = [
            fake_driver_device.make_fake_driver_device('0000:01:00.0')
        ]
        drv2.discover.return_value = [
            fake_driver_device.make_fake_driver_device('0000:01:00.0')
        ]
        self.rt.acc_drivers = {'nvme': drv1, 'ssd': drv2}

        self.assertRaises(exception.InvalidConfiguration, self.rt.init_host)
        drv1.init_host.assert_called_once_with()
        drv2.init_host.assert_called_once_with()
        drv1.discover.assert_called_once_with()
        drv2.discover.assert_called_once_with()

    def test_duplicate_device_raises(self):
        device_lists = {
            'nvme': [
                fake_driver_device.make_fake_driver_device('0000:01:00.0')
            ],
            'ssd': [
                fake_driver_device.make_fake_driver_device('0000:01:00.0')
            ],
        }
        self.assertRaises(
            exception.InvalidConfiguration,
            self.rt.check_duplicate_devices,
            device_lists,
        )

    def test_duplicate_device_different_serialization_raises(self):
        """Same BDF serialized differently by two drivers is still a dup.

        pci_str_to_json emits sorted, spaced keys; other producers (e.g.
        fake.py) emit unsorted, unspaced JSON for the same address. The
        check must compare the canonical BDF, not the raw JSON string.
        """
        device_lists = {
            # sorted, spaced (pci_str_to_json output for 0000:01:00.0)
            'nvme': [
                fake_driver_device.make_fake_driver_device('0000:01:00.0')
            ],
            # unsorted, unspaced (fake.py style) - same 0000:01:00.0
            'fake': [
                fake_driver_device.make_fake_driver_device(
                    cpid_info='{"domain":"0000","bus":"01",'
                    '"device":"00","function":"0"}'
                )
            ],
        }
        self.assertRaises(
            exception.InvalidConfiguration,
            self.rt.check_duplicate_devices,
            device_lists,
        )

    def test_no_duplicate_passes(self):
        device_lists = {
            'nvme': [
                fake_driver_device.make_fake_driver_device('0000:01:00.0')
            ],
            'pci': [
                fake_driver_device.make_fake_driver_device('0000:02:00.0')
            ],
        }
        self.rt.check_duplicate_devices(device_lists)
