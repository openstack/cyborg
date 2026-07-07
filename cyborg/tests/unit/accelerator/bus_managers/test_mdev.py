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

"""Unit tests for the MdevBusManager sysfs handler."""

import pathlib

from unittest import mock

import fixtures

from cyborg.accelerator.bus_managers.mdev import MdevBusManager
from cyborg.accelerator.bus_managers.mdev import MdevParentDevice
from cyborg.accelerator.bus_managers.mdev import MdevType
from cyborg.tests import base
from cyborg.tests.local_fixtures.mdev_sysfs import MdevSysfsFixture


class TestMdevBusManagerDiscover(base.TestCase):
    """Tests for MdevBusManager.discover_parent_devices."""

    def setUp(self):
        super().setUp()
        self.sysfs = self.useFixture(
            MdevSysfsFixture(
                devices=[
                    MdevParentDevice(address='0000:06:00.0'),
                    MdevParentDevice(address='0000:07:00.0'),
                ],
            ),
        ).path
        self.mgr = MdevBusManager(sysfs_path=self.sysfs)

    def test_filter_none_returns_empty(self):
        result = self.mgr.discover_parent_devices(pci_filter=None)
        self.assertEqual([], result)

    def test_filter_wildcard_returns_all(self):
        result = self.mgr.discover_parent_devices(
            pci_filter=['*'],
        )
        addresses = [d.address for d in result]
        self.assertEqual(
            ['0000:06:00.0', '0000:07:00.0'],
            addresses,
        )

    def test_filter_specific_address(self):
        result = self.mgr.discover_parent_devices(
            pci_filter=['0000:06:00.0'],
        )
        self.assertEqual(1, len(result))
        self.assertEqual('0000:06:00.0', result[0].address)

    def test_filter_specific_address_no_match(self):
        result = self.mgr.discover_parent_devices(
            pci_filter=['0000:99:00.0'],
        )
        self.assertEqual([], result)

    def test_nonexistent_sysfs_path(self):
        mgr = MdevBusManager(
            sysfs_path=self.sysfs + '/nonexistent/path',
        )
        result = mgr.discover_parent_devices(
            pci_filter=['*'],
        )
        self.assertEqual([], result)

    def test_empty_sysfs_directory(self):
        empty_sysfs = self.useFixture(fixtures.TempDir()).path
        mgr = MdevBusManager(sysfs_path=empty_sysfs)
        result = mgr.discover_parent_devices(
            pci_filter=['*'],
        )
        self.assertEqual([], result)

    @mock.patch(
        'pathlib.Path.iterdir',
        side_effect=OSError('denied'),
        autospec=True,
    )
    def test_listdir_oserror(self, mock_listdir):
        result = self.mgr.discover_parent_devices(
            pci_filter=['*'],
        )
        self.assertEqual([], result)

    def test_filter_empty_list_returns_empty(self):
        result = self.mgr.discover_parent_devices(
            pci_filter=[],
        )
        self.assertEqual([], result)

    def test_filter_multiple_addresses(self):
        result = self.mgr.discover_parent_devices(
            pci_filter=['0000:06:00.0', '0000:07:00.0'],
        )
        addresses = [d.address for d in result]
        self.assertEqual(
            ['0000:06:00.0', '0000:07:00.0'],
            addresses,
        )

    def test_filter_multiple_addresses_partial_match(self):
        result = self.mgr.discover_parent_devices(
            pci_filter=['0000:06:00.0', '0000:99:00.0'],
        )
        self.assertEqual(1, len(result))
        self.assertEqual('0000:06:00.0', result[0].address)


class TestMdevBusManagerTypes(base.TestCase):
    """Tests for MdevBusManager.get_mdev_types."""

    def setUp(self):
        super().setUp()
        self.pci_addr = '0000:06:00.0'
        self.sysfs = self.useFixture(
            MdevSysfsFixture(
                devices=[
                    MdevParentDevice(
                        address=self.pci_addr,
                        mdev_types=[
                            MdevType(
                                type_name='nvidia-319',
                                name='GRID V100-1Q',
                                available_instances=16,
                                created_instances=0,
                                device_api='vfio-pci',
                                description='num_heads=4, ram=1024M',
                            ),
                            MdevType(
                                type_name='nvidia-320',
                                name='GRID V100-2Q',
                                available_instances=8,
                                created_instances=0,
                                device_api='vfio-pci',
                                description='',
                            ),
                        ],
                    ),
                ],
            ),
        ).path
        self.mgr = MdevBusManager(sysfs_path=self.sysfs)

    def test_filter_none_returns_empty(self):
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=None,
        )
        self.assertEqual([], result)

    def test_filter_wildcard_returns_all(self):
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['*'],
        )
        self.assertEqual(2, len(result))
        type_names = [t.type_name for t in result]
        self.assertIn('nvidia-319', type_names)
        self.assertIn('nvidia-320', type_names)

    def test_filter_specific_type(self):
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['nvidia-319'],
        )
        self.assertEqual(1, len(result))
        self.assertEqual('nvidia-319', result[0].type_name)

    def test_type_attributes(self):
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['nvidia-319'],
        )
        self.assertEqual(1, len(result))
        mdev_type = result[0]
        self.assertEqual('nvidia-319', mdev_type.type_name)
        self.assertEqual('GRID V100-1Q', mdev_type.name)
        self.assertEqual(16, mdev_type.available_instances)
        self.assertEqual(0, mdev_type.created_instances)
        self.assertEqual('vfio-pci', mdev_type.device_api)
        self.assertEqual(
            'num_heads=4, ram=1024M',
            mdev_type.description,
        )

    def test_missing_description_defaults_to_empty(self):
        """nvidia-320 was created without a description file."""
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['nvidia-320'],
        )
        self.assertEqual(1, len(result))
        self.assertEqual('', result[0].description)

    def test_created_instances_counting(self):
        addr = '0000:07:00.0'
        sysfs = self.useFixture(
            MdevSysfsFixture(
                devices=[
                    MdevParentDevice(
                        address=addr,
                        mdev_types=[
                            MdevType(
                                type_name='nvidia-319',
                                name='GRID V100-1Q',
                                available_instances=13,
                                created_instances=3,
                                device_api='vfio-pci',
                                description='',
                            ),
                        ],
                    ),
                ],
            ),
        ).path
        mgr = MdevBusManager(sysfs_path=sysfs)
        result = mgr.get_mdev_types(
            addr,
            type_filter=['nvidia-319'],
        )
        self.assertEqual(1, len(result))
        self.assertEqual(3, result[0].created_instances)

    def test_created_instances_zero_when_no_devices_dir(self):
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['nvidia-319'],
        )
        self.assertEqual(1, len(result))
        self.assertEqual(0, result[0].created_instances)

    def test_nonexistent_pci_address(self):
        result = self.mgr.get_mdev_types(
            '0000:99:00.0',
            type_filter=['*'],
        )
        self.assertEqual([], result)

    def test_filter_no_matching_type(self):
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['nonexistent-type'],
        )
        self.assertEqual([], result)

    def test_missing_required_attr_skips_type(self):
        """A type missing device_api is skipped."""
        broken_type = (
            pathlib.Path(self.sysfs)
            / self.pci_addr
            / 'mdev_supported_types'
            / 'broken-type'
        )
        broken_type.mkdir(parents=True, exist_ok=True)
        (broken_type / 'name').write_text('Broken')
        (broken_type / 'available_instances').write_text('4')
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['*'],
        )
        type_names = [t.type_name for t in result]
        self.assertNotIn('broken-type', type_names)
        self.assertIn('nvidia-319', type_names)
        self.assertIn('nvidia-320', type_names)

    def test_invalid_available_instances_skips_type(self):
        """A type with non-integer available_instances is skipped."""
        bad_type = (
            pathlib.Path(self.sysfs)
            / self.pci_addr
            / 'mdev_supported_types'
            / 'bad-avail'
        )
        bad_type.mkdir(parents=True, exist_ok=True)
        (bad_type / 'available_instances').write_text(
            'not_a_number',
        )
        (bad_type / 'device_api').write_text('vfio-pci')
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['*'],
        )
        type_names = [t.type_name for t in result]
        self.assertNotIn('bad-avail', type_names)
        self.assertIn('nvidia-319', type_names)

    def test_missing_name_defaults_to_empty(self):
        """A type without a name file gets empty string."""
        nameless = (
            pathlib.Path(self.sysfs)
            / self.pci_addr
            / 'mdev_supported_types'
            / 'nameless-type'
        )
        nameless.mkdir(parents=True, exist_ok=True)
        (nameless / 'available_instances').write_text('2')
        (nameless / 'device_api').write_text('vfio-pci')
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['nameless-type'],
        )
        self.assertEqual(1, len(result))
        self.assertEqual('', result[0].name)

    def test_filter_empty_list_returns_empty(self):
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=[],
        )
        self.assertEqual([], result)

    def test_missing_available_instances_skips_type(self):
        """A type missing available_instances is skipped."""
        broken_type = (
            pathlib.Path(self.sysfs)
            / self.pci_addr
            / 'mdev_supported_types'
            / 'no-avail'
        )
        broken_type.mkdir(parents=True, exist_ok=True)
        (broken_type / 'device_api').write_text('vfio-pci')
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['*'],
        )
        type_names = [t.type_name for t in result]
        self.assertNotIn('no-avail', type_names)
        self.assertIn('nvidia-319', type_names)

    @mock.patch(
        'pathlib.Path.iterdir',
        side_effect=OSError('denied'),
        autospec=True,
    )
    def test_get_mdev_types_listdir_oserror(
        self,
        mock_listdir,
    ):
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['*'],
        )
        self.assertEqual([], result)

    def test_created_instances_listdir_oserror(self):
        devices_dir = (
            pathlib.Path(self.sysfs)
            / self.pci_addr
            / 'mdev_supported_types'
            / 'nvidia-319'
            / 'devices'
        )
        devices_dir.mkdir(parents=True, exist_ok=True)
        devices_dir.chmod(0o000)
        self.addCleanup(devices_dir.chmod, 0o755)
        result = self.mgr.get_mdev_types(
            self.pci_addr,
            type_filter=['nvidia-319'],
        )
        self.assertEqual(1, len(result))
        self.assertEqual(0, result[0].created_instances)
