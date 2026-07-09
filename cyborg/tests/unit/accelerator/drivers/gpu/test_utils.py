# Copyright 2018 Beijing Lenovo Software Ltd.
#
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

from unittest import mock

from oslo_serialization import jsonutils

from cyborg import conf
from cyborg.accelerator.bus_managers import mdev
from cyborg.accelerator.drivers.gpu import utils
from cyborg.accelerator.drivers.gpu.nvidia import driver
from cyborg.accelerator.drivers.gpu.nvidia import sysinfo
from cyborg.conf import devices as conf_devices
from cyborg.tests import base
from cyborg.tests.local_fixtures import mdev_sysfs


CONF = conf.CONF

NVIDIA_GPU_INFO = (
    "0000:00:06.0 3D controller [0302]: NVIDIA Corporation "
    "GP100GL [Tesla P100 PCIe 12GB] [10de:15f7] (rev a1)"
)

NVIDIA_T4_GPU_INFO = (
    "0000:af:00.0 3D controller [0302]: NVIDIA Corporation "
    "TU104GL [Tesla T4] [10de:1eb8] (rev a1)"
)

NVIDIA_A100_PF_INFO = (
    "0000:3b:00.0 3D controller [0302]: NVIDIA Corporation "
    "GA100 [A100 PCIe 40GB] [10de:20f1] (rev a1)"
)

NVIDIA_A100_VF_INFO = (
    "0000:3b:00.4 3D controller [0302]: NVIDIA Corporation "
    "GA100 [A100 PCIe 40GB] [10de:20f1] (rev a1)"
)


class TestGPUDriverUtils(base.TestCase):
    def setUp(self):
        super().setUp()

    def _enable_vgpu_type(self, vgpu_type, device_addresses):
        self.cfg_fixture.config(
            enabled_vgpu_types=[vgpu_type], group="gpu_devices"
        )
        conf_devices.register_dynamic_opts(sysinfo.CONF)
        self.cfg_fixture.config(
            device_addresses=device_addresses,
            group="vgpu_%s" % vgpu_type,
        )

    @mock.patch('cyborg.accelerator.common.utils.lspci_privileged')
    def test_discover_vendors(self, mock_devices):
        mock_devices.return_value = NVIDIA_GPU_INFO
        gpu_vendors = utils.discover_vendors()
        self.assertEqual(1, len(gpu_vendors))

    @mock.patch('cyborg.accelerator.common.utils.lspci_privileged')
    def test_discover_gpus_report_pGPU(self, mock_devices_for_vendor):
        """test nvidia pGPU discover"""
        mock_devices_for_vendor.return_value = NVIDIA_GPU_INFO
        self.set_defaults(host='host-192-168-32-195', debug=True)

        nvidia = driver.NVIDIAGPUDriver()
        gpu_list = nvidia.discover()

        self.assertEqual(1, len(gpu_list))
        attach_handle_list = [
            {
                'attach_type': 'PCI',
                'attach_info': '{"bus": "00", '
                '"device": "06", '
                '"domain": "0000", '
                '"function": "0"}',
                'in_use': False,
            }
        ]
        attribute_list = [
            {'key': 'rc', 'value': 'PGPU'},
            {'key': 'trait0', 'value': 'OWNER_CYBORG'},
            {'key': 'trait1', 'value': 'CUSTOM_NVIDIA_15F7'},
        ]
        expected = {
            'vendor': '10de',
            'type': 'GPU',
            'model': 'NVIDIA Corporation GP100GL [Tesla P100 PCIe 12GB]',
            'std_board_info': {
                "controller": "3D controller",
                "product_id": "15f7",
            },
            'vendor_board_info': {"vendor_info": "gpu_vb_info"},
            'deployable_list': [
                {
                    'num_accelerators': 1,
                    'driver_name': 'NVIDIA',
                    'name': 'host-192-168-32-195_0000:00:06.0',
                    'attach_handle_list': attach_handle_list,
                    'attribute_list': attribute_list,
                },
            ],
            'controlpath_id': {
                'cpid_info': '{"bus": "00", '
                '"device": "06", '
                '"domain": "0000", '
                '"function": "0"}',
                'cpid_type': 'PCI',
            },
        }
        gpu_obj = gpu_list[0]
        gpu_dict = gpu_obj.as_dict()
        gpu_dep_list = gpu_dict['deployable_list']
        gpu_attach_handle_list = gpu_dep_list[0].as_dict()[
            'attach_handle_list'
        ]
        gpu_attribute_list = gpu_dep_list[0].as_dict()['attribute_list']
        attri_obj_data = []
        [attri_obj_data.append(attr.as_dict()) for attr in gpu_attribute_list]
        attribute_actual_data = sorted(attri_obj_data, key=lambda i: i['key'])
        self.assertEqual(expected['vendor'], gpu_dict['vendor'])
        self.assertEqual(expected['model'], gpu_dict['model'])
        self.assertEqual(
            expected['controlpath_id'], gpu_dict['controlpath_id']
        )
        self.assertEqual(
            expected['std_board_info'],
            jsonutils.loads(gpu_dict['std_board_info']),
        )
        self.assertEqual(
            expected['vendor_board_info'],
            jsonutils.loads(gpu_dict['vendor_board_info']),
        )
        self.assertEqual(
            expected['deployable_list'][0]['num_accelerators'],
            gpu_dep_list[0].as_dict()['num_accelerators'],
        )
        self.assertEqual(
            expected['deployable_list'][0]['name'],
            gpu_dep_list[0].as_dict()['name'],
        )
        self.assertEqual(
            expected['deployable_list'][0]['driver_name'],
            gpu_dep_list[0].as_dict()['driver_name'],
        )
        self.assertEqual(
            attach_handle_list[0], gpu_attach_handle_list[0].as_dict()
        )
        self.assertEqual(attribute_list, attribute_actual_data)

    @mock.patch('cyborg.accelerator.common.utils.lspci_privileged')
    def test_discover_gpus_report_vGPU(
        self,
        mock_devices_for_vendor,
    ):
        """test nvidia vGPU discover"""
        mock_devices_for_vendor.return_value = NVIDIA_T4_GPU_INFO
        mdev_fix = self.useFixture(
            mdev_sysfs.MdevSysfsFixture(
                devices=[
                    mdev.MdevParentDevice(
                        address='0000:af:00.0',
                        mdev_types=[
                            mdev.MdevType(
                                type_name='nvidia-223',
                                name='GRID T4-1B',
                                available_instances=1,
                                created_instances=17,
                                device_api='vfio-pci',
                                description='',
                            )
                        ],
                    ),
                ]
            ),
        )
        mgr = mdev.MdevBusManager(sysfs_path=mdev_fix.path)
        self.set_defaults(
            host='host-192-168-32-195',
            debug=True,
        )
        self._enable_vgpu_type("nvidia-223", ["0000:af:00.0"])
        nvidia = driver.NVIDIAGPUDriver(mdev_bus_manager=mgr)
        gpu_list = nvidia.discover()

        self.assertEqual(1, len(gpu_list))
        attach_handle_list = [
            {
                'attach_type': 'MDEV',
                'attach_info': '{"asked_type": "nvidia-223", '
                '"bus": "af", '
                '"device": "00", '
                '"domain": "0000", '
                '"function": "0", '
                '"vgpu_mark": "nvidia-223_0"}',
                'in_use': False,
            }
        ]
        attribute_list = [
            {'key': 'rc', 'value': 'VGPU'},
            {'key': 'trait0', 'value': 'OWNER_CYBORG'},
            {'key': 'trait1', 'value': 'CUSTOM_NVIDIA_1EB8_T4_1B'},
        ]
        expected = {
            'vendor': '10de',
            'type': 'GPU',
            'std_board_info': {
                "controller": "3D controller",
                "product_id": "1eb8",
            },
            'vendor_board_info': {"vendor_info": "gpu_vb_info"},
            'deployable_list': [
                {
                    'num_accelerators': 18,
                    'driver_name': 'NVIDIA',
                    'name': ('host-192-168-32-195_0000:af:00.0'),
                    'attach_handle_list': attach_handle_list,
                    'attribute_list': attribute_list,
                },
            ],
            'controlpath_id': {
                'cpid_info': '{"bus": "af", '
                '"device": "00", '
                '"domain": "0000", '
                '"function": "0"}',
                'cpid_type': 'PCI',
            },
        }
        gpu_obj = gpu_list[0]
        gpu_dict = gpu_obj.as_dict()
        gpu_dep_list = gpu_dict['deployable_list']
        gpu_attach_handle_list = gpu_dep_list[0].as_dict()[
            'attach_handle_list'
        ]
        gpu_attribute_list = gpu_dep_list[0].as_dict()['attribute_list']
        attri_obj_data = []
        for attr in gpu_attribute_list:
            attri_obj_data.append(attr.as_dict())
        attribute_actual_data = sorted(
            attri_obj_data,
            key=lambda i: i['key'],
        )
        self.assertEqual(
            expected['vendor'],
            gpu_dict['vendor'],
        )
        self.assertEqual(
            expected['controlpath_id'],
            gpu_dict['controlpath_id'],
        )
        self.assertEqual(
            expected['std_board_info'],
            jsonutils.loads(gpu_dict['std_board_info']),
        )
        self.assertEqual(
            expected['vendor_board_info'],
            jsonutils.loads(gpu_dict['vendor_board_info']),
        )
        self.assertEqual(
            expected['deployable_list'][0]['num_accelerators'],
            gpu_dep_list[0].as_dict()['num_accelerators'],
        )
        self.assertEqual(
            expected['deployable_list'][0]['name'],
            gpu_dep_list[0].as_dict()['name'],
        )
        self.assertEqual(
            expected['deployable_list'][0]['driver_name'],
            gpu_dep_list[0].as_dict()['driver_name'],
        )
        self.assertEqual(
            attach_handle_list[0],
            gpu_attach_handle_list[0].as_dict(),
        )
        self.assertEqual(
            attribute_list,
            attribute_actual_data,
        )

    @mock.patch('cyborg.accelerator.drivers.gpu.nvidia.sysinfo._is_vf')
    @mock.patch('cyborg.accelerator.common.utils.lspci_privileged')
    def test_discover_gpus_filters_vf_devices(
        self, mock_devices_for_vendor, mock_is_vf
    ):
        """Test that VF devices are filtered when filter_sriov_vfs=True."""
        mock_devices_for_vendor.return_value = (
            NVIDIA_A100_PF_INFO + '\n' + NVIDIA_A100_VF_INFO
        )
        mock_is_vf.side_effect = lambda addr: addr == '0000:3b:00.4'
        self.set_defaults(host='host-192-168-32-195', debug=True)
        self.set_defaults(filter_sriov_vfs=True, group='gpu_devices')

        nvidia = driver.NVIDIAGPUDriver()
        gpu_list = nvidia.discover()

        self.assertEqual(1, len(gpu_list))
        gpu_dict = gpu_list[0].as_dict()
        dep_name = gpu_dict['deployable_list'][0].as_dict()['name']
        self.assertIn('0000:3b:00.0', dep_name)

    @mock.patch('cyborg.accelerator.drivers.gpu.nvidia.sysinfo._is_vf')
    @mock.patch('cyborg.accelerator.common.utils.lspci_privileged')
    def test_discover_gpus_vf_not_filtered_by_default(
        self, mock_devices_for_vendor, mock_is_vf
    ):
        """Test that VFs are reported when filter_sriov_vfs=False (default)."""
        mock_devices_for_vendor.return_value = (
            NVIDIA_A100_PF_INFO + '\n' + NVIDIA_A100_VF_INFO
        )
        mock_is_vf.side_effect = lambda addr: addr == '0000:3b:00.4'
        self.set_defaults(host='host-192-168-32-195', debug=True)

        nvidia = driver.NVIDIAGPUDriver()
        gpu_list = nvidia.discover()

        self.assertEqual(2, len(gpu_list))
        mock_is_vf.assert_not_called()

    @mock.patch('cyborg.accelerator.drivers.gpu.nvidia.sysinfo._is_vf')
    @mock.patch('cyborg.accelerator.common.utils.lspci_privileged')
    def test_discover_gpus_continues_on_is_vf_oserror(
        self, mock_devices_for_vendor, mock_is_vf
    ):
        """Test discovery continues when _is_vf raises OSError."""
        mock_devices_for_vendor.return_value = (
            NVIDIA_A100_PF_INFO + '\n' + NVIDIA_A100_VF_INFO
        )
        mock_is_vf.side_effect = OSError('device busy')
        self.set_defaults(host='host-192-168-32-195', debug=True)
        self.set_defaults(filter_sriov_vfs=True, group='gpu_devices')

        nvidia = driver.NVIDIAGPUDriver()
        gpu_list = nvidia.discover()

        self.assertEqual(2, len(gpu_list))
        self.assertEqual(2, mock_is_vf.call_count)


class TestIsVf(base.TestCase):
    @mock.patch('os.path.exists', return_value=True)
    def test_is_vf_returns_true_when_physfn_exists(self, mock_exists):
        self.assertTrue(sysinfo._is_vf('0000:3b:00.4'))
        mock_exists.assert_called_once_with(
            '/sys/bus/pci/devices/0000:3b:00.4/physfn'
        )

    @mock.patch('os.path.exists', return_value=False)
    def test_is_vf_returns_false_for_pf(self, mock_exists):
        self.assertFalse(sysinfo._is_vf('0000:3b:00.0'))
        mock_exists.assert_called_once_with(
            '/sys/bus/pci/devices/0000:3b:00.0/physfn'
        )

    @mock.patch('os.path.exists', side_effect=OSError('device busy'))
    def test_is_vf_returns_false_on_oserror(self, mock_exists):
        self.assertFalse(sysinfo._is_vf('0000:3b:00.4'))
        mock_exists.assert_called_once_with(
            '/sys/bus/pci/devices/0000:3b:00.4/physfn'
        )
