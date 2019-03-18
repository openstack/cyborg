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

import mock
import os
import subprocess

import fixtures

from cyborg.accelerator.drivers.fpga.intel import sysinfo
from cyborg.accelerator.drivers.fpga.intel.driver import IntelFPGADriver
from cyborg.tests import base
from cyborg.tests.unit.accelerator.drivers.fpga.intel import prepare_test_data


class TestIntelFPGADriver(base.TestCase):

    def setUp(self):
        super(TestIntelFPGADriver, self).setUp()
        self.syspath = sysinfo.SYS_FPGA
        sysinfo.SYS_FPGA = "/sys/class/fpga"
        tmp_sys_dir = self.useFixture(fixtures.TempDir())
        prepare_test_data.create_fake_sysfs(tmp_sys_dir.path)
        sysinfo.SYS_FPGA = os.path.join(
            tmp_sys_dir.path, sysinfo.SYS_FPGA.split("/", 1)[-1])

    def tearDown(self):
        super(TestIntelFPGADriver, self).tearDown()
        sysinfo.SYS_FPGA = self.syspath

    def test_discover(self):
        attach_handle_list = [
            [
                {'attach_type': 'pci',
                 'attach_info': '0000:be:00.0',
                 'in_use': False}
            ],
            [
                {'attach_type': 'pci',
                 'attach_info': '0000:5e:00.1',
                 'in_use': False}
            ]
        ]
        expected = [{'vendor': '0x8086',
                     'type': 'FPGA',
                     'model': '0xbcc0',
                     'deployable_list':
                         [
                             {'num_accelerators': 1,
                              'name': 'intel-fpga-dev.1',
                              'attach_handle_list': attach_handle_list[0]
                              },
                         ],
                     'controlpath_id':
                         {'cpid_info': '0000:be:00.0',
                          'cpid_type': 'pci'}},
                    {'vendor': '0x8086',
                     'type': 'FPGA',
                     'model': '0xbcc0',
                     'deployable_list':
                         [
                             {'num_accelerators': 1,
                              'name': 'intel-fpga-dev.2',
                              'attach_handle_list': attach_handle_list[1]
                              },
                         ],
                     'controlpath_id':
                         {'cpid_info': '0000:5e:00.0',
                          'cpid_type': 'pci'}}]
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
                             fpga_dict['controlpath_id'].as_dict())
            self.assertEqual(expected[i]['deployable_list'][0]
                             ['num_accelerators'],
                             fpga_dep_list[0].as_dict()['num_accelerators'])
            self.assertEqual(attach_handle_list[i][0],
                             fpga_attach_handle_list[0].as_dict())

    @mock.patch.object(subprocess, 'Popen', autospec=True)
    def test_intel_program(self, mock_popen):

        class p(object):
            returncode = 0

            def wait(self):
                pass

        b = "0x5e"
        d = "0x00"
        f = "0x0"
        expect_cmd = ['sudo', '/usr/bin/fpgaconf', '-b', b,
                      '-d', d, '-f', f, '/path/image']
        mock_popen.return_value = p()
        intel = IntelFPGADriver()
        # program VF
        intel.program("0000:5e:00.1", "/path/image")
        mock_popen.assert_called_with(expect_cmd, stdout=subprocess.PIPE)

        # program PF
        intel.program("0000:5e:00.0", "/path/image")
        mock_popen.assert_called_with(expect_cmd, stdout=subprocess.PIPE)
