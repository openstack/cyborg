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

"""Unit tests for the generic mdev driver."""

import fixtures

from oslo_serialization import jsonutils

from cyborg.accelerator.bus_managers import mdev
from cyborg.accelerator.drivers.mdev import driver as mdev_driver
from cyborg.common import constants
from cyborg.common import exception
from cyborg.tests import base
from cyborg.tests.local_fixtures import mdev_sysfs


class TestGenericMdevDriver(base.TestCase):
    """Tests for the GenericMdevDriver."""

    def setUp(self):
        super().setUp()
        self.sysfs = self.useFixture(fixtures.TempDir()).path
        self.set_defaults(host='fake-mdev-host', debug=True)

    def _setup_devices(self, devices):
        """Create a fake mdev sysfs tree from device objects.

        :param devices: List of MdevParentDevice instances.
        """
        self.sysfs = self.useFixture(
            mdev_sysfs.MdevSysfsFixture(devices=devices),
        ).path

    def _mtype(
        self,
        type_name='nvidia-319',
        name='GRID V100-1Q',
        available_instances=0,
        created_instances=0,
        device_api='vfio-pci',
        description='',
    ):
        """Build an MdevType with common test defaults.

        :param type_name: mdev type name.
        :param name: Human-readable name.
        :param available_instances: Available instance count.
        :param created_instances: Created instance count.
        :param device_api: Device API string.
        :param description: Description text.
        :returns: An MdevType instance.
        """
        return mdev.MdevType(
            type_name=type_name,
            name=name,
            available_instances=available_instances,
            created_instances=created_instances,
            device_api=device_api,
            description=description,
        )

    def _set_device_spec(self, specs):
        """Set [mdev] device_spec from a list of JSON strings.

        :param specs: List of JSON-encoded device_spec entries.
        """
        self.flags(device_spec=specs, group='mdev')

    def _make_driver(self):
        """Create a GenericMdevDriver with test paths.

        :returns: A GenericMdevDriver instance.
        """
        mgr = mdev.MdevBusManager(sysfs_path=self.sysfs)
        return mdev_driver.GenericMdevDriver(
            bus_manager=mgr,
        )

    def _discover(self):
        """Run discovery with test bus manager and paths.

        :returns: List of DriverDevice objects.
        """
        return self._make_driver().discover()

    def test_single_type_single_parent(self):
        """One mdev type on one parent device."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=16),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        self.assertEqual(1, len(devs))
        dev = devs[0]
        dev_dict = dev.as_dict()
        self.assertEqual(
            constants.DEVICE_MDEV,
            dev_dict['type'],
        )
        # Check deployable
        dep = dev_dict['deployable_list'][0]
        dep_dict = dep.as_dict()
        self.assertEqual(16, dep_dict['num_accelerators'])
        self.assertEqual(
            'fake-mdev-host_0000:06:00.0_nvidia-319',
            dep_dict['name'],
        )
        self.assertEqual('mdev', dep_dict['driver_name'])

    def test_multiple_types_per_parent_raises(self):
        """Two mdev types for the same parent address are rejected."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=16),
                        self._mtype(
                            type_name='nvidia-320',
                            name='GRID V100-2Q',
                            available_instances=8,
                        ),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-320"}',
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            self._discover,
        )

    def test_multiple_parents(self):
        """Same mdev type on two different parents."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=16),
                    ],
                ),
                mdev.MdevParentDevice(
                    address='0000:07:00.0',
                    mdev_types=[
                        self._mtype(available_instances=8),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "*", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        self.assertEqual(2, len(devs))
        addrs = sorted(
            jsonutils.loads(
                d.as_dict()['controlpath_id']['cpid_info'],
            )['bus']
            for d in devs
        )
        self.assertEqual(['06', '07'], addrs)

    def test_empty_config_returns_empty(self):
        """No device_spec entries yields no devices."""
        self._set_device_spec([])
        devs = self._discover()
        self.assertEqual([], devs)

    def test_max_instances_cap(self):
        """max_instances caps num_accelerators."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=16),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "max_instances": 4}',
            ]
        )
        devs = self._discover()
        self.assertEqual(1, len(devs))
        dep = devs[0].as_dict()['deployable_list'][0]
        dep_dict = dep.as_dict()
        self.assertEqual(4, dep_dict['num_accelerators'])
        self.assertEqual(
            4,
            len(dep_dict['attach_handle_list']),
        )

    def test_max_instances_higher_than_available(self):
        """max_instances higher than total does not inflate."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=3),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "max_instances": 100}',
            ]
        )
        devs = self._discover()
        dep = devs[0].as_dict()['deployable_list'][0]
        self.assertEqual(
            3,
            dep.as_dict()['num_accelerators'],
        )

    def test_custom_resource_class(self):
        """resource_class override from config is used."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=4),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "resource_class": "CUSTOM_MY_VGPU"}',
            ]
        )
        devs = self._discover()
        dep = devs[0].as_dict()['deployable_list'][0]
        attrs = dep.as_dict()['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        rc_vals = [a['value'] for a in attr_data if a['key'] == 'rc']
        self.assertEqual(['CUSTOM_MY_VGPU'], rc_vals)

    def test_custom_traits(self):
        """Extra traits from config are added."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=2),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "traits": ["CUSTOM_FAST", "CUSTOM_GPU"]}',
            ]
        )
        devs = self._discover()
        dep = devs[0].as_dict()['deployable_list'][0]
        attrs = dep.as_dict()['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        trait_vals = [
            a['value'] for a in attr_data if a['key'].startswith('trait')
        ]
        self.assertIn(constants.OWNER_CYBORG, trait_vals)
        self.assertIn('CUSTOM_FAST', trait_vals)
        self.assertIn('CUSTOM_GPU', trait_vals)

    def test_custom_traits_normalized(self):
        """Traits without CUSTOM_ prefix are normalized."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=1),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "traits": ["my-fast-trait"]}',
            ]
        )
        devs = self._discover()
        dep = devs[0].as_dict()['deployable_list'][0]
        attrs = dep.as_dict()['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        trait_vals = [
            a['value'] for a in attr_data if a['key'].startswith('trait')
        ]
        self.assertIn('CUSTOM_MY_FAST_TRAIT', trait_vals)

    def test_resource_class_normalization(self):
        """Hyphens in type name become underscores."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=2),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        dep = devs[0].as_dict()['deployable_list'][0]
        attrs = dep.as_dict()['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        rc_vals = [a['value'] for a in attr_data if a['key'] == 'rc']
        self.assertEqual(['CUSTOM_MDEV_NVIDIA_319'], rc_vals)

    def test_attach_handle_format(self):
        """Attach handles use AH_TYPE_MDEV with asked_type."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=2),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        dep = devs[0].as_dict()['deployable_list'][0]
        ah_list = dep.as_dict()['attach_handle_list']
        self.assertEqual(2, len(ah_list))
        ah = ah_list[0].as_dict()
        self.assertEqual(
            constants.AH_TYPE_MDEV,
            ah['attach_type'],
        )
        self.assertFalse(ah['in_use'])
        info = jsonutils.loads(ah['attach_info'])
        self.assertEqual('nvidia-319', info['asked_type'])
        self.assertEqual('06', info['bus'])

    def test_deployable_name_format(self):
        """Deployable name is hostname_pci_address_type_name."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=1),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        dep = devs[0].as_dict()['deployable_list'][0]
        self.assertEqual(
            'fake-mdev-host_0000:06:00.0_nvidia-319',
            dep.as_dict()['name'],
        )

    def test_created_instances_counted(self):
        """num_accelerators = available + created."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(
                            available_instances=10,
                            created_instances=3,
                        ),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        dep = devs[0].as_dict()['deployable_list'][0]
        self.assertEqual(
            13,
            dep.as_dict()['num_accelerators'],
        )

    def test_controlpath_id_type(self):
        """Control path ID uses PCI type."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=1),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        cpid = devs[0].as_dict()['controlpath_id']
        self.assertEqual('PCI', cpid['cpid_type'])

    def test_driver_class_discover(self):
        """GenericMdevDriver.discover() works end-to-end."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=4),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        driver = self._make_driver()
        devs = driver.discover()
        self.assertEqual(1, len(devs))
        self.assertEqual(
            constants.DEVICE_MDEV,
            devs[0].as_dict()['type'],
        )

    def test_owner_cyborg_trait_always_present(self):
        """OWNER_CYBORG trait is always included."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=1),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        dep = devs[0].as_dict()['deployable_list'][0]
        attrs = dep.as_dict()['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        trait_vals = [
            a['value'] for a in attr_data if a['key'].startswith('trait')
        ]
        self.assertIn(constants.OWNER_CYBORG, trait_vals)

    def test_resource_class_override_normalized(self):
        """resource_class with hyphens is normalized."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=1),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "resource_class": "my-rc"}',
            ]
        )
        devs = self._discover()
        dep = devs[0].as_dict()['deployable_list'][0]
        attrs = dep.as_dict()['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        rc_vals = [a['value'] for a in attr_data if a['key'] == 'rc']
        self.assertEqual(['CUSTOM_MY_RC'], rc_vals)

    def test_vendor_id_from_sysfs(self):
        """Vendor ID is read from sysfs by the bus manager."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    vendor='10de',
                    mdev_types=[
                        self._mtype(available_instances=1),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        self.assertEqual('10de', devs[0].as_dict()['vendor'])

    def test_product_id_from_sysfs(self):
        """Product ID is read from sysfs by the bus manager."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    model='1db4',
                    mdev_types=[
                        self._mtype(available_instances=1),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        self.assertEqual('1db4', devs[0].as_dict()['model'])

    def test_sysfs_id_fallback_unknown(self):
        """Vendor and model fall back when sysfs is absent."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=1),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        dev_dict = devs[0].as_dict()
        self.assertEqual('unknown', dev_dict['vendor'])
        self.assertEqual('unknown', dev_dict['model'])

    def test_invalid_json_device_spec_raises(self):
        """Invalid JSON in device_spec raises."""
        self._set_device_spec(['not-valid-json'])
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            self._discover,
        )

    def test_missing_address_in_spec_raises(self):
        """Spec missing address raises."""
        self._set_device_spec(
            [
                '{"mdev_type": "nvidia-319"}',
            ]
        )
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            self._discover,
        )

    def test_missing_mdev_type_in_spec_raises(self):
        """Spec missing mdev_type raises."""
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0"}',
            ]
        )
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            self._discover,
        )

    def test_invalid_max_instances_raises(self):
        """Invalid max_instances value raises an error."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=8),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "max_instances": "abc"}',
            ]
        )
        self.assertRaises(exception.InvalidMdevDevSpecConfig, self._discover)

    def test_config_present_hardware_absent(self):
        """Config references device not present in sysfs."""
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        devs = self._discover()
        self.assertEqual([], devs)

    def test_traits_as_string_raises(self):
        """Traits specified as a string raises an error."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=1),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "traits": "CUSTOM_FAST"}',
            ]
        )
        self.assertRaises(exception.InvalidMdevDevSpecConfig, self._discover)

    def test_traits_as_null_raises(self):
        """Traits specified as null raise an error."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=1),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "traits": null}',
            ]
        )
        self.assertRaises(exception.InvalidMdevDevSpecConfig, self._discover)

    def test_negative_max_instances_raises(self):
        """Negative max_instances raises an error."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=8),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "max_instances": -1}',
            ]
        )
        self.assertRaises(exception.InvalidMdevDevSpecConfig, self._discover)

    def test_duplicate_device_spec_uses_first(self):
        """Duplicate (address, mdev_type) uses first entry."""
        self._setup_devices(
            [
                mdev.MdevParentDevice(
                    address='0000:06:00.0',
                    mdev_types=[
                        self._mtype(available_instances=16),
                    ],
                ),
            ]
        )
        self._set_device_spec(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "max_instances": 2}',
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "max_instances": 5}',
            ]
        )
        devs = self._discover()
        self.assertEqual(1, len(devs))
        dep = devs[0].as_dict()['deployable_list'][0]
        self.assertEqual(
            2,
            dep.as_dict()['num_accelerators'],
        )
