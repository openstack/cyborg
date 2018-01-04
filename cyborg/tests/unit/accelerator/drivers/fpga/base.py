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

from cyborg.accelerator.drivers.fpga.base import FPGADriver
from cyborg.accelerator.drivers.fpga.intel import sysinfo
from cyborg.tests import base
from cyborg.tests.unit.accelerator.drivers.fpga.intel import prepare_test_data


class TestFPGADriver(base.TestCase):

    def setUp(self):
        super(TestFPGADriver, self).setUp()
        self.syspath = sysinfo.SYS_FPGA
        sysinfo.SYS_FPGA = "/sys/class/fpga"
        tmp_sys_dir = self.useFixture(fixtures.TempDir())
        prepare_test_data.create_fake_sysfs(tmp_sys_dir.path)
        sysinfo.SYS_FPGA = os.path.join(
            tmp_sys_dir.path, sysinfo.SYS_FPGA.split("/", 1)[-1])

    def tearDown(self):
        super(TestFPGADriver, self).tearDown()
        sysinfo.SYS_FPGA = self.syspath

    def test_create(self):
        FPGADriver.create("intel")
        self.assertRaises(LookupError, FPGADriver.create, "xilinx")

    def test_discover(self):
        d = FPGADriver()
        self.assertRaises(NotImplementedError, d.discover)

    def test_program(self):
        d = FPGADriver()
        self.assertRaises(NotImplementedError, d.program, "path", "image")

    def test_intel_discover(self):
        expect = [{'function': 'pf', 'assignable': False, 'pr_num': '1',
                   'vendor_id': '0x8086', 'devices': '0000:5e:00.0',
                   'regions': [{
                       'function': 'vf', 'assignable': True,
                       'product_id': '0xbcc1',
                       'name': 'intel-fpga-dev.2',
                       'parent_devices': '0000:5e:00.0',
                       'path': '%s/intel-fpga-dev.2' % sysinfo.SYS_FPGA,
                       'vendor_id': '0x8086',
                       'devices': '0000:5e:00.1'}],
                   'name': 'intel-fpga-dev.0',
                   'parent_devices': '',
                   'path': '%s/intel-fpga-dev.0' % sysinfo.SYS_FPGA,
                   'product_id': '0xbcc0'},
                  {'function': 'pf', 'assignable': True, 'pr_num': '0',
                   'vendor_id': '0x8086', 'devices': '0000:be:00.0',
                   'name': 'intel-fpga-dev.1',
                   'parent_devices': '',
                   'path': '%s/intel-fpga-dev.1' % sysinfo.SYS_FPGA,
                   'product_id': '0xbcc0'}]
        expect.sort()

        intel = FPGADriver.create("intel")
        fpgas = intel.discover()
        fpgas.sort()
        self.assertEqual(2, len(fpgas))
        self.assertEqual(fpgas, expect)

    @mock.patch.object(subprocess, 'Popen', autospec=True)
    def test_intel_program(self, mock_popen):

        class p(object):
            returncode = 0

            def wait(self):
                pass

        b = "0x5e"
        d = "0x00"
        f = "0x0"
        expect_cmd = ['sudo', 'fpgaconf', '-b', b,
                      '-d', d, '-f', f, '/path/image']
        mock_popen.return_value = p()
        intel = FPGADriver.create("intel")
        # program VF
        intel.program("0000:5e:00.1", "/path/image")
        mock_popen.assert_called_with(expect_cmd, stdout=subprocess.PIPE)

        # program PF
        intel.program("0000:5e:00.0", "/path/image")
        mock_popen.assert_called_with(expect_cmd, stdout=subprocess.PIPE)
