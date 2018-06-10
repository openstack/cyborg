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

from oslo_serialization import jsonutils

import mock
import copy
import subprocess

from cyborg.accelerator.drivers.gpu import utils
from cyborg import objects
from cyborg.tests import base

NVIDIA_GPU_INFO = "0000:00:06.0 3D controller [0302]: NVIDIA Corporation GP100GL " \
                  "[Tesla P100 PCIe 12GB] [10de:15f7] (rev a1)"


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

    @mock.patch.object(subprocess, 'Popen', autospec=True)
    def test_discover_vendors(self, mock_popen):
        mock_popen.return_value = self.p
        gpu_venders = utils.discover_vendors()
        self.assertEqual(1, len(gpu_venders))

    @mock.patch.object(subprocess, 'Popen', autospec=True)
    def test_discover_gpus(self, mock_popen):
        mock_popen.return_value = self.p
        vender_id = '10de'
        gpu_list = utils.discover_gpus(vender_id)
        self.assertEqual(1, len(gpu_list))
        attach_handle_list = [
            {'attach_type': 'PCI',
             'attach_info': '0000:00:06.0',
             'in_use': False}
        ]
        expected = {
            'vendor': '10de',
            'type': 'GPU',
            'std_board_info':
                {"controller": "3D controller", "product_id": "15f7"},
            'deployable_list':
                [
                    {
                        'num_accelerators': 1,
                        'name': 'NVIDIA Corporation GP100GL '
                                '[Tesla P100 PCIe 12GB]_0000:00:06.0',
                        'attach_handle_list': attach_handle_list
                    },
                ],
            'controlpath_id': {'cpid_info': '0000:00:06.0', 'cpid_type': 'PCI'}
        }
        gpu_obj = gpu_list[0]
        gpu_dict = gpu_obj.as_dict()
        gpu_dep_list = gpu_dict['deployable_list']
        gpu_attach_handle_list = \
            gpu_dep_list[0].as_dict()['attach_handle_list']
        self.assertEqual(expected['vendor'], gpu_dict['vendor'])
        self.assertEqual(expected['controlpath_id'],
                         gpu_dict['controlpath_id'].as_dict())
        self.assertEqual(expected['std_board_info'],
                         jsonutils.loads(gpu_dict['std_board_info']))
        self.assertEqual(expected['deployable_list'][0]['num_accelerators'],
                         gpu_dep_list[0].as_dict()['num_accelerators'])
        self.assertEqual(expected['deployable_list'][0]['name'],
                         gpu_dep_list[0].as_dict()['name'])
        self.assertEqual(attach_handle_list[0],
                         gpu_attach_handle_list[0].as_dict())
