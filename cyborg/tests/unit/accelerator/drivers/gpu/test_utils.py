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

from cyborg.accelerator.drivers.gpu import utils
from cyborg.tests import base

NVIDIA_GPU_INFO = "0000:00:06.0 3D controller [0302]: NVIDIA Corporation " \
                  "GP100GL [Tesla P100 PCIe 12GB] [10de:15f7] (rev a1)"


class stdout(object):
    def readlines(self):
        return [NVIDIA_GPU_INFO]


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
    def test_discover_gpus(self, mock_devices_for_vendor):
        mock_devices_for_vendor.return_value = self.p.stdout.readlines()
        self.set_defaults(host='host-192-168-32-195', debug=True)
        vendor_id = '10de'
        gpu_list = utils.discover_gpus(vendor_id)
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
            {'key': 'trait0', 'value': 'CUSTOM_GPU_NVIDIA'},
            {'key': 'trait1', 'value': 'CUSTOM_GPU_PRODUCT_ID_15F7'},
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
