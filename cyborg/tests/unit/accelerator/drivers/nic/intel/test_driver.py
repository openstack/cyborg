# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

from unittest import mock

import fixtures

from cyborg.accelerator.drivers.nic.intel import sysinfo
from cyborg.accelerator.drivers.nic.intel.driver import IntelNICDriver
from cyborg.common import exception
from cyborg.conf import devices as conf_devices
from cyborg.tests import base
from cyborg.tests.unit.accelerator.drivers.nic.intel import prepare_test_data


class TestIntelNICDriver(base.TestCase):
    def setUp(self):
        super().setUp()
        self.pcipath = sysinfo.PCI_DEVICES_PATH_PATTERN
        tmp_sys_dir = self.useFixture(fixtures.TempDir())
        prepare_test_data.create_fake_sysfs(tmp_sys_dir.path)
        tmp_path = tmp_sys_dir.path
        sysinfo.PCI_DEVICES_PATH_PATTERN = os.path.join(
            tmp_path, sysinfo.PCI_DEVICES_PATH_PATTERN.split("/", 1)[-1]
        )

    def tearDown(self):
        super().tearDown()
        sysinfo.PCI_DEVICES_PATH_PATTERN = self.pcipath

    @mock.patch("cyborg.accelerator.common.utils.get_ifname_by_pci_address")
    def test_discover(self, mock_device_ifname):
        mock_device_ifname.return_value = "ethx"
        attach_handle_list = [
            [
                {
                    'attach_type': 'PCI',
                    'attach_info': '{"bus": "05", '
                    '"device": "01", '
                    '"domain": "0000", '
                    '"function": "0"}',
                    'in_use': False,
                }
            ],
            [
                {
                    'attach_type': 'PCI',
                    'attach_info': '{"bus": "06", '
                    '"device": "00", '
                    '"domain": "0000", '
                    '"function": "0"}',
                    'in_use': False,
                }
            ],
        ]
        attribute_list = [
            [
                {"key": "rc", "value": "CUSTOM_NIC"},
                {"key": "trait0", "value": "CUSTOM_VF"},
            ],
            [
                {"key": "rc", "value": "CUSTOM_NIC"},
                {"key": "trait0", "value": "CUSTOM_PF"},
            ],
        ]
        expected = [
            {
                'vendor': '0x8086',
                'type': 'NIC',
                'deployable_list': [
                    {
                        'num_accelerators': 1,
                        'name': '0000:05:01.0',
                        'attach_handle_list': attach_handle_list[0],
                        'attribute_list': attribute_list[0],
                    },
                ],
                'controlpath_id': {
                    'cpid_info': '{"bus": "05", '
                    '"device": "00", '
                    '"domain": "0000", '
                    '"function": "0"}',
                    'cpid_type': 'PCI',
                },
            },
            {
                'vendor': '0x8086',
                'type': 'NIC',
                'deployable_list': [
                    {
                        'num_accelerators': 1,
                        'name': '0000:06:00.0',
                        'attach_handle_list': attach_handle_list[1],
                        'attribute_list': attribute_list[1],
                    },
                ],
                'controlpath_id': {
                    'cpid_info': '{"bus": "06", '
                    '"device": "00", '
                    '"domain": "0000", '
                    '"function": "0"}',
                    'cpid_type': 'PCI',
                },
            },
        ]
        intel = IntelNICDriver()
        nics = intel.discover()
        list.sort(nics, key=lambda x: x._obj_deployable_list[0].name)
        self.assertEqual(2, len(nics))
        for i in range(len(nics)):
            nic_dict = nics[i].as_dict()
            nic_dep_list = nic_dict['deployable_list']
            nic_attach_handle_list = nic_dep_list[0].as_dict()[
                'attach_handle_list'
            ]
            nic_attribute_list = nic_dep_list[0].as_dict()['attribute_list']
            self.assertEqual(expected[i]['vendor'], nic_dict['vendor'])
            self.assertEqual(
                expected[i]['controlpath_id'], nic_dict['controlpath_id']
            )
            self.assertEqual(
                expected[i]['deployable_list'][0]['num_accelerators'],
                nic_dep_list[0].as_dict()['num_accelerators'],
            )
            self.assertEqual(1, len(nic_attach_handle_list))
            self.assertEqual(
                attach_handle_list[i][0], nic_attach_handle_list[0].as_dict()
            )
            self.assertEqual(
                attribute_list[i][0], nic_attribute_list[0].as_dict()
            )

    @mock.patch("cyborg.accelerator.common.utils.get_ifname_by_pci_address")
    def test_discover_device_addresses_filter(self, mock_device_ifname):
        # With device_addresses set, only the listed PF is discovered; the
        # other matching PF (e.g. a management interface) is excluded.
        mock_device_ifname.return_value = "ethx"
        self.cfg_fixture.config(
            enabled_nic_types=["x710_static"], group="nic_devices"
        )
        conf_devices.register_dynamic_opts(sysinfo.CONF)
        self.cfg_fixture.config(
            device_addresses=["0000:05:00.0"], group="x710_static"
        )
        intel = IntelNICDriver()
        nics = intel.discover()
        self.assertEqual(1, len(nics))
        self.assertEqual(
            '{"bus": "05", "device": "00", "domain": "0000", "function": "0"}',
            nics[0].as_dict()["controlpath_id"]["cpid_info"],
        )

    @mock.patch("cyborg.accelerator.common.utils.get_ifname_by_pci_address")
    def test_discover_vf_address_filter(self, mock_device_ifname):
        # PF0 (0000:05:00.0) owns a VF (0000:05:01.0). Listing the VF address
        # (not the PF) exposes exactly that VF as a deployable, with its PF
        # kept only as the controlpath. PF1 (no VF, not listed) is dropped.
        mock_device_ifname.return_value = "ethx"
        self.cfg_fixture.config(
            enabled_nic_types=["x710_static"], group="nic_devices"
        )
        conf_devices.register_dynamic_opts(sysinfo.CONF)
        self.cfg_fixture.config(
            device_addresses=["0000:05:01.0"], group="x710_static"
        )
        intel = IntelNICDriver()
        nics = intel.discover()
        self.assertEqual(1, len(nics))
        nic = nics[0].as_dict()
        # PF0 remains the controlpath.
        self.assertEqual(
            '{"bus": "05", "device": "00", "domain": "0000", "function": "0"}',
            nic["controlpath_id"]["cpid_info"],
        )
        # Only the listed VF is exposed as a deployable.
        self.assertEqual(1, len(nic["deployable_list"]))
        dep = nic["deployable_list"][0].as_dict()
        attach_handle = dep["attach_handle_list"][0].as_dict()
        self.assertEqual(
            '{"bus": "05", "device": "01", "domain": "0000", "function": "0"}',
            attach_handle["attach_info"],
        )

    @mock.patch("cyborg.accelerator.common.utils.get_ifname_by_pci_address")
    def test_discover_non_sriov_pf_address(self, mock_device_ifname):
        # PF1 (0000:06:00.0) has no VFs. Listing its address exposes the PF
        # itself as the sole deployable (there are no VFs to expose).
        mock_device_ifname.return_value = "ethx"
        self.cfg_fixture.config(
            enabled_nic_types=["x710_static"], group="nic_devices"
        )
        conf_devices.register_dynamic_opts(sysinfo.CONF)
        self.cfg_fixture.config(
            device_addresses=["0000:06:00.0"], group="x710_static"
        )
        intel = IntelNICDriver()
        nics = intel.discover()
        self.assertEqual(1, len(nics))
        nic = nics[0].as_dict()
        self.assertEqual(
            '{"bus": "06", "device": "00", "domain": "0000", "function": "0"}',
            nic["controlpath_id"]["cpid_info"],
        )
        self.assertEqual(1, len(nic["deployable_list"]))
        dep = nic["deployable_list"][0].as_dict()
        attach_handle = dep["attach_handle_list"][0].as_dict()
        self.assertEqual(
            '{"bus": "06", "device": "00", "domain": "0000", "function": "0"}',
            attach_handle["attach_info"],
        )

    def test_discover_invalid_device_address_raises(self):
        # A malformed PCI address in device_addresses is rejected at parse
        # time rather than silently ignored.
        self.cfg_fixture.config(
            enabled_nic_types=["x710_static"], group="nic_devices"
        )
        conf_devices.register_dynamic_opts(sysinfo.CONF)
        self.cfg_fixture.config(
            device_addresses=["not-a-pci-address"], group="x710_static"
        )
        intel = IntelNICDriver()
        self.assertRaises(
            exception.PciDeviceWrongAddressFormat, intel.discover
        )
