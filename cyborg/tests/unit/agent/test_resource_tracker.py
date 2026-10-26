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

from unittest import mock

from cyborg.accelerator.drivers.driver import GenericDriver
from cyborg.agent.resource_tracker import ResourceTracker
from cyborg.common import exception
from cyborg.conductor import rpcapi as cond_api
from cyborg.conf import CONF
from cyborg.tests import base
from cyborg.tests.unit import fake_driver_device


class TestResourceTracker(base.TestCase):
    """Test Agent ResourceTracker"""

    def setUp(self):
        super().setUp()
        self.host = CONF.host
        self.cond_api = cond_api.ConductorAPI()
        self.rt = ResourceTracker(self.host, self.cond_api)

    def test_update_usage(self):
        """Update the resource usage and stats after a change in an
        instance
        """
        # FIXME(Shaohe Feng) need add testcase. How to check the fpgas
        # has stored into DB by conductor correctly?
        pass

    def test_initialize_acc_drivers(self):
        enabled_drivers = ['intel_fpga_driver']
        self.rt._initialize_drivers(enabled_drivers=enabled_drivers)
        drivers = self.rt.acc_drivers
        self.assertEqual(len(drivers), len(enabled_drivers))

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
    @mock.patch(
        'cyborg.agent.resource_tracker.ExtensionManager', autospec=True
    )
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
            self.rt.update_usage(None)
            m.assert_called_once_with(None, 'fake-mini', mock.ANY)
        mock_log.error.assert_called_once_with(
            'Unable to report usage: %s', m.side_effect
        )

    def test_init_drivers_calls_each(self):
        drv1 = mock.create_autospec(GenericDriver, instance=True)
        drv2 = mock.create_autospec(GenericDriver, instance=True)
        self.rt.acc_drivers = {'a': drv1, 'b': drv2}
        self.rt.init_drivers()
        drv1.init_host.assert_called_once()
        drv2.init_host.assert_called_once()

    def test_init_drivers_propagates_exception(self):
        drv = mock.create_autospec(GenericDriver, instance=True)
        drv.init_host.side_effect = exception.InvalidConfiguration(
            reason='nvme-cli not found'
        )
        self.rt.acc_drivers = {'nvme': drv}
        self.assertRaises(
            exception.InvalidConfiguration,
            self.rt.init_drivers,
        )

    def test_init_host_rejects_duplicate_devices(self):
        drv1 = mock.create_autospec(GenericDriver, instance=True)
        drv2 = mock.create_autospec(GenericDriver, instance=True)
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
