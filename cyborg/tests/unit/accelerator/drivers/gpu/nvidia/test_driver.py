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

"""Unit tests for the NVIDIA GPU driver."""

from unittest import mock

from oslo_serialization import jsonutils

from cyborg import conf as cyborg_conf
from cyborg.accelerator.bus_managers import mdev
from cyborg.accelerator.drivers.gpu.nvidia import driver
from cyborg.accelerator.drivers.gpu.nvidia import sysinfo
from cyborg.common import constants
from cyborg.common import exception
from cyborg.conf import devices as conf_devices
from cyborg.tests import base
from cyborg.tests.local_fixtures import mdev_sysfs


CONF = cyborg_conf.CONF

NVIDIA_P100_LSPCI = (
    "0000:00:06.0 3D controller [0302]: NVIDIA Corporation "
    "GP100GL [Tesla P100 PCIe 12GB] [10de:15f7] (rev a1)"
)

NVIDIA_T4_LSPCI = (
    "0000:af:00.0 3D controller [0302]: NVIDIA Corporation "
    "TU104GL [Tesla T4] [10de:1eb8] (rev a1)"
)


class TestNvidiaGPUDriver(base.TestCase):
    """Tests for the NVIDIA GPU driver discovery."""

    def setUp(self):
        super().setUp()
        self.mdev_fixture = self.useFixture(mdev_sysfs.MdevSysfsFixture())
        self.set_defaults(host='test-host', debug=True)

    def _make_driver(self):
        mgr = mdev.MdevBusManager(sysfs_path=self.mdev_fixture.path)
        return driver.NVIDIAGPUDriver(mdev_bus_manager=mgr)

    def _enable_vgpu_type(self, vgpu_type, device_addresses):
        self.cfg_fixture.config(
            enabled_vgpu_types=[vgpu_type], group="gpu_devices"
        )
        conf_devices.register_dynamic_opts(sysinfo.CONF)
        self.cfg_fixture.config(
            device_addresses=device_addresses,
            group="vgpu_%s" % vgpu_type,
        )

    def test_get_supported_vgpu_types_case_insensitive_duplicate(self):
        # Two vgpu types configured with the same physical address, but
        # written in different case, must still be caught as a duplicate
        # rather than silently accepted as two distinct devices.
        self.cfg_fixture.config(
            enabled_vgpu_types=["nvidia-35", "nvidia-36"],
            group="gpu_devices",
        )
        conf_devices.register_dynamic_opts(sysinfo.CONF)
        self.cfg_fixture.config(
            device_addresses=["0000:AF:00.0"], group="vgpu_nvidia-35"
        )
        self.cfg_fixture.config(
            device_addresses=["0000:af:00.0"], group="vgpu_nvidia-36"
        )
        self.assertRaises(
            exception.InvalidvGPUConfig, sysinfo._get_supported_vgpu_types
        )

    def test_get_vgpu_type_per_pgpu_case_insensitive(self):
        # The operator wrote the address in uppercase in config; the
        # discovered pGPU address (as reported by the driver) is lowercase.
        # This must still resolve to a vGPU type instead of silently
        # falling through to pGPU (passthrough) registration.
        self._enable_vgpu_type("nvidia-35", ["0000:AF:00.0"])
        supported, mapping = sysinfo._get_supported_vgpu_types()
        vgpu_type = sysinfo._get_vgpu_type_per_pgpu(
            "0000:af:00.0", supported, mapping
        )
        self.assertEqual("nvidia-35", vgpu_type)

    def test_get_vgpu_type_per_pgpu_no_match(self):
        # An address that isn't configured for any vgpu type resolves to
        # None (falls back to pGPU registration), same as before this fix.
        self._enable_vgpu_type("nvidia-35", ["0000:AF:00.0"])
        supported, mapping = sysinfo._get_supported_vgpu_types()
        vgpu_type = sysinfo._get_vgpu_type_per_pgpu(
            "0000:ff:00.0", supported, mapping
        )
        self.assertIsNone(vgpu_type)

    @mock.patch(
        'cyborg.accelerator.common.utils.lspci_privileged',
        autospec=True,
    )
    def test_discover_pgpu(self, mock_lspci):
        """pGPU discovery produces correct driver objects."""
        mock_lspci.return_value = NVIDIA_P100_LSPCI
        nvidia = self._make_driver()
        gpu_list = nvidia.discover()

        self.assertEqual(1, len(gpu_list))
        dev = gpu_list[0].as_dict()
        self.assertEqual('10de', dev['vendor'])
        self.assertEqual(constants.DEVICE_GPU, dev['type'])

        dep = dev['deployable_list'][0].as_dict()
        self.assertEqual(1, dep['num_accelerators'])
        self.assertEqual('NVIDIA', dep['driver_name'])
        self.assertEqual(
            'test-host_0000:00:06.0',
            dep['name'],
        )

        # Check attach handle
        ah = dep['attach_handle_list'][0].as_dict()
        self.assertEqual(constants.AH_TYPE_PCI, ah['attach_type'])
        self.assertFalse(ah['in_use'])

        # Check control path ID
        cpid = dev['controlpath_id']
        self.assertEqual('PCI', cpid['cpid_type'])
        cpid_info = jsonutils.loads(cpid['cpid_info'])
        self.assertEqual('0000', cpid_info['domain'])
        self.assertEqual('00', cpid_info['bus'])

    @mock.patch(
        'cyborg.accelerator.common.utils.lspci_privileged',
        autospec=True,
    )
    def test_discover_pgpu_traits(self, mock_lspci):
        """pGPU discovery generates correct traits."""
        mock_lspci.return_value = NVIDIA_P100_LSPCI
        nvidia = self._make_driver()
        gpu_list = nvidia.discover()

        dep = gpu_list[0].as_dict()['deployable_list'][0]
        attrs = dep.as_dict()['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        rc_vals = [a['value'] for a in attr_data if a['key'] == 'rc']
        trait_vals = [
            a['value'] for a in attr_data if a['key'].startswith('trait')
        ]

        self.assertEqual(['PGPU'], rc_vals)
        self.assertIn(constants.OWNER_CYBORG, trait_vals)
        self.assertIn('CUSTOM_NVIDIA_15F7', trait_vals)

    @mock.patch(
        'cyborg.accelerator.common.utils.lspci_privileged',
        autospec=True,
    )
    def test_discover_vgpu_with_mdev_bus_manager(
        self,
        mock_lspci,
    ):
        """vGPU discovery delegates to MdevBusManager."""
        mock_lspci.return_value = NVIDIA_T4_LSPCI
        self.mdev_fixture = self.useFixture(
            mdev_sysfs.MdevSysfsFixture(
                devices=[
                    mdev.MdevParentDevice(
                        address='0000:af:00.0',
                        mdev_types=[
                            mdev.MdevType(
                                type_name='nvidia-223',
                                name='GRID T4-1B',
                                available_instances=8,
                                created_instances=2,
                                device_api='vfio-pci',
                                description='',
                            )
                        ],
                    ),
                ]
            ),
        )
        self._enable_vgpu_type('nvidia-223', ['0000:af:00.0'])

        nvidia = self._make_driver()
        gpu_list = nvidia.discover()

        self.assertEqual(1, len(gpu_list))
        dev = gpu_list[0].as_dict()
        self.assertEqual('10de', dev['vendor'])

        dep = dev['deployable_list'][0].as_dict()
        self.assertEqual(10, dep['num_accelerators'])
        self.assertEqual(
            10,
            len(dep['attach_handle_list']),
        )
        self.assertEqual('NVIDIA', dep['driver_name'])
        self.assertEqual(
            'test-host_0000:af:00.0',
            dep['name'],
        )

    @mock.patch(
        'cyborg.accelerator.common.utils.lspci_privileged',
        autospec=True,
    )
    def test_discover_vgpu_traits(self, mock_lspci):
        """vGPU discovery generates correct traits."""
        mock_lspci.return_value = NVIDIA_T4_LSPCI
        self.mdev_fixture = self.useFixture(
            mdev_sysfs.MdevSysfsFixture(
                devices=[
                    mdev.MdevParentDevice(
                        address='0000:af:00.0',
                        mdev_types=[
                            mdev.MdevType(
                                type_name='nvidia-223',
                                name='GRID T4-1B',
                                available_instances=4,
                                created_instances=0,
                                device_api='vfio-pci',
                                description='',
                            )
                        ],
                    ),
                ]
            ),
        )
        self._enable_vgpu_type('nvidia-223', ['0000:af:00.0'])

        nvidia = self._make_driver()
        gpu_list = nvidia.discover()

        dep = gpu_list[0].as_dict()['deployable_list'][0]
        attrs = dep.as_dict()['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        rc_vals = [a['value'] for a in attr_data if a['key'] == 'rc']
        trait_vals = [
            a['value'] for a in attr_data if a['key'].startswith('trait')
        ]

        self.assertEqual(['VGPU'], rc_vals)
        self.assertIn(constants.OWNER_CYBORG, trait_vals)
        self.assertIn(
            'CUSTOM_NVIDIA_1EB8_T4_1B',
            trait_vals,
        )

    @mock.patch(
        'cyborg.accelerator.common.utils.lspci_privileged',
        autospec=True,
    )
    def test_discover_vgpu_attach_handles(
        self,
        mock_lspci,
    ):
        """vGPU attach handles use MDEV type."""
        mock_lspci.return_value = NVIDIA_T4_LSPCI
        self.mdev_fixture = self.useFixture(
            mdev_sysfs.MdevSysfsFixture(
                devices=[
                    mdev.MdevParentDevice(
                        address='0000:af:00.0',
                        mdev_types=[
                            mdev.MdevType(
                                type_name='nvidia-223',
                                name='GRID T4-1B',
                                available_instances=2,
                                created_instances=0,
                                device_api='vfio-pci',
                                description='',
                            )
                        ],
                    ),
                ]
            ),
        )
        self._enable_vgpu_type('nvidia-223', ['0000:af:00.0'])

        nvidia = self._make_driver()
        gpu_list = nvidia.discover()

        dep = gpu_list[0].as_dict()['deployable_list'][0]
        ah_list = dep.as_dict()['attach_handle_list']
        self.assertEqual(2, len(ah_list))

        ah = ah_list[0].as_dict()
        self.assertEqual(
            constants.AH_TYPE_MDEV,
            ah['attach_type'],
        )
        self.assertFalse(ah['in_use'])
        info = jsonutils.loads(ah['attach_info'])
        self.assertEqual('nvidia-223', info['asked_type'])
        self.assertEqual('af', info['bus'])

    @mock.patch(
        'cyborg.accelerator.common.utils.lspci_privileged',
        autospec=True,
    )
    def test_discover_vgpu_invalid_type_raises(
        self,
        mock_lspci,
    ):
        """Invalid vGPU type not in sysfs raises."""
        mock_lspci.return_value = NVIDIA_T4_LSPCI
        # nvidia-999 does not exist in the fake sysfs
        self._enable_vgpu_type('nvidia-999', ['0000:af:00.0'])

        nvidia = self._make_driver()
        self.assertRaises(
            exception.InvalidVGPUType,
            nvidia.discover,
        )

    @mock.patch(
        'cyborg.accelerator.common.utils.lspci_privileged',
        autospec=True,
    )
    def test_discover_vgpu_only_available(
        self,
        mock_lspci,
    ):
        """vGPU with no created instances only counts available."""
        mock_lspci.return_value = NVIDIA_T4_LSPCI
        self.mdev_fixture = self.useFixture(
            mdev_sysfs.MdevSysfsFixture(
                devices=[
                    mdev.MdevParentDevice(
                        address='0000:af:00.0',
                        mdev_types=[
                            mdev.MdevType(
                                type_name='nvidia-223',
                                name='GRID T4-1B',
                                available_instances=16,
                                created_instances=0,
                                device_api='vfio-pci',
                                description='',
                            )
                        ],
                    ),
                ]
            ),
        )

        self._enable_vgpu_type('nvidia-223', ['0000:af:00.0'])

        nvidia = self._make_driver()
        gpu_list = nvidia.discover()

        dep = gpu_list[0].as_dict()['deployable_list'][0]
        self.assertEqual(
            16,
            dep.as_dict()['num_accelerators'],
        )

    @mock.patch(
        'cyborg.accelerator.common.utils.lspci_privileged',
        autospec=True,
    )
    def test_discover_no_vgpu_config_returns_pgpu(
        self,
        mock_lspci,
    ):
        """Without vGPU config, GPUs are reported as pGPU."""
        mock_lspci.return_value = NVIDIA_T4_LSPCI

        nvidia = self._make_driver()
        gpu_list = nvidia.discover()

        self.assertEqual(1, len(gpu_list))
        dep = gpu_list[0].as_dict()['deployable_list'][0]
        attrs = dep.as_dict()['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        rc_vals = [a['value'] for a in attr_data if a['key'] == 'rc']
        self.assertEqual(['PGPU'], rc_vals)

    @mock.patch(
        'cyborg.accelerator.drivers.gpu.nvidia.sysinfo._is_vf',
        autospec=True,
    )
    @mock.patch(
        'cyborg.accelerator.common.utils.lspci_privileged',
        autospec=True,
    )
    def test_discover_filters_vf_with_vgpu(
        self,
        mock_lspci,
        mock_is_vf,
    ):
        """VF filtering works alongside vGPU discovery."""
        vf_lspci = (
            "0000:af:00.4 3D controller [0302]: "
            "NVIDIA Corporation "
            "TU104GL [Tesla T4] [10de:1eb8] (rev a1)"
        )
        mock_lspci.return_value = NVIDIA_T4_LSPCI + '\n' + vf_lspci
        mock_is_vf.side_effect = lambda addr: addr == '0000:af:00.4'
        self.set_defaults(
            filter_sriov_vfs=True,
            group='gpu_devices',
        )

        nvidia = self._make_driver()
        gpu_list = nvidia.discover()

        self.assertEqual(1, len(gpu_list))
        dep = gpu_list[0].as_dict()['deployable_list'][0]
        self.assertIn(
            '0000:af:00.0',
            dep.as_dict()['name'],
        )
