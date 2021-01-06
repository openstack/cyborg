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

import sys
from unittest import mock

from oslo_serialization import jsonutils

import cyborg
from cyborg.accelerator.drivers.gpu.nvidia.driver import NVIDIAGPUDriver
from cyborg.accelerator.drivers.gpu import utils
from cyborg.tests import base


CONF = cyborg.conf.CONF

NVIDIA_GPU_INFO = "0000:00:06.0 3D controller [0302]: NVIDIA Corporation " \
                  "GP100GL [Tesla P100 PCIe 12GB] [10de:15f7] (rev a1)"

NVIDIA_T4_GPU_INFO = "0000:af:00.0 3D controller [0302]: NVIDIA Corporation "\
                     "TU104GL [Tesla T4] [10de:1eb8] (rev a1)"

NVIDIA_T4_SUPPORTED_MDEV_TYPES = ['nvidia-222', 'nvidia-223', 'nvidia-224',
                                  'nvidia-225', 'nvidia-226', 'nvidia-227',
                                  'nvidia-228', 'nvidia-229', 'nvidia-230',
                                  'nvidia-231', 'nvidia-232', 'nvidia-233',
                                  'nvidia-234', 'nvidia-252', 'nvidia-319',
                                  'nvidia-320', 'nvidia-321']

BUILTIN = '__builtin__' if (sys.version_info[0] < 3) else '__builtins__'


class stdout(object):
    def readlines(self):
        return [NVIDIA_GPU_INFO]

    def readlines_T4(self):
        return [NVIDIA_T4_GPU_INFO]


class p(object):
    def __init__(self):
        self.stdout = stdout()

    def wait(self):
        pass


class TestGPUDriverUtils(base.TestCase):

    def setUp(self):
        super(TestGPUDriverUtils, self).setUp()
        self.p = p()

    @mock.patch('cyborg.accelerator.drivers.gpu.utils.lspci_privileged')
    def test_discover_vendors(self, mock_devices):
        mock_devices.return_value = self.p.stdout.readlines()
        gpu_vendors = utils.discover_vendors()
        self.assertEqual(1, len(gpu_vendors))

    @mock.patch('cyborg.accelerator.drivers.gpu.utils.lspci_privileged')
    def test_discover_gpus_report_pGPU(self, mock_devices_for_vendor):
        """test nvidia pGPU discover"""
        mock_devices_for_vendor.return_value = self.p.stdout.readlines()
        self.set_defaults(host='host-192-168-32-195', debug=True)

        nvidia = NVIDIAGPUDriver()
        gpu_list = nvidia.discover()

        self.assertEqual(1, len(gpu_list))
        attach_handle_list = [
            {'attach_type': 'PCI',
             'attach_info': '{"bus": "00", '
                            '"device": "06", '
                            '"domain": "0000", '
                            '"function": "0"}',
             'in_use': False}
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
            'std_board_info':
                {"controller": "3D controller", "product_id": "15f7"},
            'vendor_board_info': {"vendor_info": "gpu_vb_info"},
            'deployable_list':
                [
                    {
                        'num_accelerators': 1,
                        'driver_name': 'NVIDIA',
                        'name': 'host-192-168-32-195_0000:00:06.0',
                        'attach_handle_list': attach_handle_list,
                        'attribute_list': attribute_list
                    },
                ],
            'controlpath_id': {'cpid_info': '{"bus": "00", '
                                            '"device": "06", '
                                            '"domain": "0000", '
                                            '"function": "0"}',
                               'cpid_type': 'PCI'}
            }
        gpu_obj = gpu_list[0]
        gpu_dict = gpu_obj.as_dict()
        gpu_dep_list = gpu_dict['deployable_list']
        gpu_attach_handle_list = \
            gpu_dep_list[0].as_dict()['attach_handle_list']
        gpu_attribute_list = \
            gpu_dep_list[0].as_dict()['attribute_list']
        attri_obj_data = []
        [attri_obj_data.append(attr.as_dict()) for attr in gpu_attribute_list]
        attribute_actual_data = sorted(attri_obj_data, key=lambda i: i['key'])
        self.assertEqual(expected['vendor'], gpu_dict['vendor'])
        self.assertEqual(expected['model'], gpu_dict['model'])
        self.assertEqual(expected['controlpath_id'],
                         gpu_dict['controlpath_id'])
        self.assertEqual(expected['std_board_info'],
                         jsonutils.loads(gpu_dict['std_board_info']))
        self.assertEqual(expected['vendor_board_info'],
                         jsonutils.loads(gpu_dict['vendor_board_info']))
        self.assertEqual(expected['deployable_list'][0]['num_accelerators'],
                         gpu_dep_list[0].as_dict()['num_accelerators'])
        self.assertEqual(expected['deployable_list'][0]['name'],
                         gpu_dep_list[0].as_dict()['name'])
        self.assertEqual(expected['deployable_list'][0]['driver_name'],
                         gpu_dep_list[0].as_dict()['driver_name'])
        self.assertEqual(attach_handle_list[0],
                         gpu_attach_handle_list[0].as_dict())
        self.assertEqual(attribute_list, attribute_actual_data)

    @mock.patch('builtins.open')
    @mock.patch('os.listdir')
    @mock.patch('os.path.exists')
    @mock.patch('cyborg.accelerator.drivers.gpu.utils.lspci_privileged')
    def test_discover_gpus_report_vGPU(self, mock_devices_for_vendor,
                                       mock_path_exists,
                                       mock_supported_mdev_types,
                                       mock_open):
        """test nvidia vGPU discover"""
        mock_devices_for_vendor.return_value = self.p.stdout.readlines_T4()
        mock_path_exists.return_value = True
        mock_supported_mdev_types.return_value = NVIDIA_T4_SUPPORTED_MDEV_TYPES
        file_content_list = ['GRID T4-1B', '1']
        mock_open.side_effect = multi_mock_open(*file_content_list)
        self.set_defaults(host='host-192-168-32-195', debug=True)
        self.set_defaults(enabled_vgpu_types='nvidia-223', group='gpu_devices')
        cyborg.conf.devices.register_dynamic_opts(CONF)
        self.set_defaults(
            device_addresses=['0000:af:00.0'], group='vgpu_nvidia-223')
        nvidia = NVIDIAGPUDriver()
        gpu_list = nvidia.discover()

        self.assertEqual(1, len(gpu_list))
        attach_handle_list = [
            {'attach_type': 'MDEV',
             'attach_info': '{"asked_type": "nvidia-223", '
                            '"bus": "af", '
                            '"device": "00", '
                            '"domain": "0000", '
                            '"function": "0", '
                            '"vgpu_mark": "nvidia-223_0"}',
             'in_use': False}
        ] * 8
        attribute_list = [
            {'key': 'rc', 'value': 'VGPU'},
            {'key': 'trait0', 'value': 'OWNER_CYBORG'},
            {'key': 'trait1', 'value': 'CUSTOM_NVIDIA_1EB8_T4_1B'},
        ]
        expected = {
            'vendor': '10de',
            'type': 'GPU',
            'std_board_info':
                {"controller": "3D controller", "product_id": "1eb8"},
            'vendor_board_info': {"vendor_info": "gpu_vb_info"},
            'deployable_list':
                [
                    {
                        'num_accelerators': 18,
                        'driver_name': 'NVIDIA',
                        'name': 'host-192-168-32-195_0000:af:00.0',
                        'attach_handle_list': attach_handle_list,
                        'attribute_list': attribute_list
                    },
                ],
            'controlpath_id': {'cpid_info': '{"bus": "af", '
                                            '"device": "00", '
                                            '"domain": "0000", '
                                            '"function": "0"}',
                               'cpid_type': 'PCI'}
            }
        gpu_obj = gpu_list[0]
        gpu_dict = gpu_obj.as_dict()
        gpu_dep_list = gpu_dict['deployable_list']
        gpu_attach_handle_list = gpu_dep_list[0].as_dict()[
            'attach_handle_list']
        gpu_attribute_list = gpu_dep_list[0].as_dict()['attribute_list']
        attri_obj_data = []
        [attri_obj_data.append(attr.as_dict()) for attr in gpu_attribute_list]
        attribute_actual_data = sorted(attri_obj_data, key=lambda i: i['key'])
        self.assertEqual(expected['vendor'], gpu_dict['vendor'])
        self.assertEqual(expected['controlpath_id'],
                         gpu_dict['controlpath_id'])
        self.assertEqual(expected['std_board_info'],
                         jsonutils.loads(gpu_dict['std_board_info']))
        self.assertEqual(expected['vendor_board_info'],
                         jsonutils.loads(gpu_dict['vendor_board_info']))
        self.assertEqual(expected['deployable_list'][0]['num_accelerators'],
                         gpu_dep_list[0].as_dict()['num_accelerators'])
        self.assertEqual(expected['deployable_list'][0]['name'],
                         gpu_dep_list[0].as_dict()['name'])
        self.assertEqual(expected['deployable_list'][0]['driver_name'],
                         gpu_dep_list[0].as_dict()['driver_name'])
        self.assertEqual(attach_handle_list[0],
                         gpu_attach_handle_list[0].as_dict())
        self.assertEqual(attribute_list, attribute_actual_data)


def multi_mock_open(*file_contents):
    """Create a mock "open" that will mock open multiple files in sequence.

    : params file_contents:  a list of file contents to be returned by open

    : returns: (MagicMock) a mock opener that will return the contents of the
               first file when opened the first time, the second file when
               opened the second time, etc.
    """

    mock_files = [
        mock.mock_open(read_data=content).return_value for content in
        file_contents]
    mock_opener = mock.mock_open()
    mock_opener.side_effect = mock_files
    return mock_opener
