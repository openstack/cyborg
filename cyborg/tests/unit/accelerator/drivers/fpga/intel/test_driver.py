# Copyright 2018 Intel, Inc.
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


import fixtures
import os
from unittest import mock

from cyborg.accelerator.drivers.fpga.intel.driver import IntelFPGADriver
from cyborg.accelerator.drivers.fpga.intel import sysinfo
from cyborg.tests import base
from cyborg.tests.unit.accelerator.drivers.fpga.intel import prepare_test_data


class TestIntelFPGADriver(base.TestCase):

    def setUp(self):
        super(TestIntelFPGADriver, self).setUp()
        self.syspath = sysinfo.SYS_FPGA
        self.pcipath = sysinfo.PCI_DEVICES_PATH
        self.pcipath_pattern = sysinfo.PCI_DEVICES_PATH_PATTERN
        tmp_sys_dir = self.useFixture(fixtures.TempDir())
        prepare_test_data.create_fake_sysfs(tmp_sys_dir.path)
        tmp_path = tmp_sys_dir.path
        sysinfo.SYS_FPGA = os.path.join(
            tmp_path, sysinfo.SYS_FPGA.split("/", 1)[-1])
        sysinfo.PCI_DEVICES_PATH = os.path.join(
            tmp_path, sysinfo.PCI_DEVICES_PATH.split("/", 1)[-1])
        sysinfo.PCI_DEVICES_PATH_PATTERN = os.path.join(
            tmp_path, sysinfo.PCI_DEVICES_PATH_PATTERN.split("/", 1)[-1])

    def tearDown(self):
        super(TestIntelFPGADriver, self).tearDown()
        sysinfo.SYS_FPGA = self.syspath
        sysinfo.PCI_DEVICES_PATH = self.pcipath
        sysinfo.PCI_DEVICES_PATH_PATTERN = self.pcipath_pattern

    def test_discover(self):
        attach_handle_list = [
            [
                {'attach_type': 'PCI',
                 'attach_info': '{"bus": "5e", '
                                '"device": "00", '
                                '"domain": "0000", '
                                '"function": "1"}',
                 'in_use': False}
            ],
            [
                {'attach_type': 'PCI',
                 'attach_info': '{"bus": "be", '
                                '"device": "00", '
                                '"domain": "0000", '
                                '"function": "0"}',
                 'in_use': False}
            ]
        ]
        expected = [{'vendor': '0x8086',
                     'type': 'FPGA',
                     'model': '0xbcc0',
                     'deployable_list':
                         [
                             {'num_accelerators': 1,
                              'name': 'intel-fpga-dev_0000:5e:00.1',
                              'attach_handle_list': attach_handle_list[0]
                              },
                         ],
                     'controlpath_id':
                         {
                             'cpid_info': '{"bus": "5e", '
                                          '"device": "00", '
                                          '"domain": "0000", '
                                          '"function": "0"}',
                             'cpid_type': 'PCI'}
                     },
                    {'vendor': '0x8086',
                     'type': 'FPGA',
                     'model': '0xbcc0',
                     'deployable_list':
                         [
                             {'num_accelerators': 1,
                              'name': 'intel-fpga-dev_0000:be:00.0',
                              'attach_handle_list': attach_handle_list[1]
                              },
                         ],
                     'controlpath_id':
                         {
                             'cpid_info': '{"bus": "be", '
                                          '"device": "00", '
                                          '"domain": "0000", '
                                          '"function": "0"}',
                             'cpid_type': 'PCI'}
                     }
                    ]
        intel = IntelFPGADriver()
        fpgas = intel.discover()
        list.sort(fpgas, key=lambda x: x._obj_deployable_list[0].name)
        self.assertEqual(2, len(fpgas))
        for i in range(len(fpgas)):
            fpga_dict = fpgas[i].as_dict()
            fpga_dep_list = fpga_dict['deployable_list']
            fpga_attach_handle_list = \
                fpga_dep_list[0].as_dict()['attach_handle_list']
            self.assertEqual(expected[i]['vendor'], fpga_dict['vendor'])
            self.assertEqual(expected[i]['controlpath_id'],
                             fpga_dict['controlpath_id'])
            self.assertEqual(expected[i]['deployable_list'][0]
                             ['num_accelerators'],
                             fpga_dep_list[0].as_dict()['num_accelerators'])
            self.assertEqual(attach_handle_list[i][0],
                             fpga_attach_handle_list[0].as_dict())

    @mock.patch('cyborg.accelerator.drivers.fpga.intel.driver.'
                '_fpga_program_privileged')
    def test_intel_program(self, mock_prog):
        b = "0x5e"
        d = "0x00"
        f = "0x0"
        expect_cmd = ['--bus', b, '--device', d, '--function', f,
                      '/path/image']

        intel = IntelFPGADriver()
        cpid_info = {"domain": "0000", "bus": "5e",
                     "device": "00", "function": "0"}
        cpid = {'cpid_type': 'PCI', 'cpid_info': cpid_info}

        # program PF
        mock_prog.return_value = bytes([0])
        intel.program(cpid, "/path/image")
        mock_prog.assert_called_with(expect_cmd)
