# Copyright (c) 2018 Intel.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


"""Cyborg agent resource_tracker test cases."""

import os

import fixtures

from cyborg.accelerator.drivers.fpga import utils
from cyborg.accelerator.drivers.fpga.intel import sysinfo
from cyborg.agent.resource_tracker import ResourceTracker
from cyborg.conductor import rpcapi as cond_api
from cyborg.conf import CONF
from cyborg.tests import base
from cyborg.tests.unit.accelerator.drivers.fpga.intel import prepare_test_data


class TestResourceTracker(base.TestCase):
    """Test Agent ResourceTracker """

    def setUp(self):
        super(TestResourceTracker, self).setUp()
        self.syspath = sysinfo.SYS_FPGA
        sysinfo.SYS_FPGA = "/sys/class/fpga"
        tmp_sys_dir = self.useFixture(fixtures.TempDir())
        prepare_test_data.create_fake_sysfs(tmp_sys_dir.path)
        sysinfo.SYS_FPGA = os.path.join(
            tmp_sys_dir.path, sysinfo.SYS_FPGA.split("/", 1)[-1])
        utils.SYS_FPGA_PATH = sysinfo.SYS_FPGA
        self.host = CONF.host
        self.cond_api = cond_api.ConductorAPI()
        self.rt = ResourceTracker(self.host, self.cond_api)

    def tearDown(self):
        super(TestResourceTracker, self).tearDown()
        sysinfo.SYS_FPGA = self.syspath
        utils.SYS_FPGA_PATH = self.syspath

    def test_update_usage(self):
        """Update the resource usage and stats after a change in an
        instance
        """
        # FIXME(Shaohe Feng) need add testcase. How to check the fpgas
        # has stored into DB by conductor correctly?
        pass

    def test_get_fpga_devices(self):
        expect = {
            '0000:5e:00.0': {
                'function': 'pf', 'assignable': False, 'pr_num': '1',
                'name': 'intel-fpga-dev.0', 'vendor_id': '0x8086',
                'devices': '0000:5e:00.0',
                'regions': [{
                    'function': 'vf', 'assignable': True,
                    'name': 'intel-fpga-dev.2', 'vendor_id': '0x8086',
                    'devices': '0000:5e:00.1',
                    'parent_devices': '0000:5e:00.0',
                    'path': '%s/intel-fpga-dev.2' % sysinfo.SYS_FPGA,
                    'product_id': '0xbcc1'}],
                'parent_devices': '',
                'path': '%s/intel-fpga-dev.0' % sysinfo.SYS_FPGA,
                'product_id': '0xbcc0'},
            '0000:5e:00.1': {
                'function': 'vf', 'assignable': True,
                'name': 'intel-fpga-dev.2', 'vendor_id': '0x8086',
                'devices': '0000:5e:00.1',
                'parent_devices': '0000:5e:00.0',
                'path': '%s/intel-fpga-dev.2' % sysinfo.SYS_FPGA,
                'product_id': '0xbcc1'},
            '0000:be:00.0': {
                'function': 'pf', 'assignable': True, 'pr_num': '0',
                'name': 'intel-fpga-dev.1', 'vendor_id': '0x8086',
                'devices': '0000:be:00.0', 'parent_devices': '',
                'path': '%s/intel-fpga-dev.1' % sysinfo.SYS_FPGA,
                'product_id': '0xbcc0'}}
        fpgas = self.rt._get_fpga_devices()
        self.assertDictEqual(expect, fpgas)
