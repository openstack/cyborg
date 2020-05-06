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

import os

from cyborg.accelerator.drivers.qat.intel import sysinfo

from cyborg.accelerator.drivers.qat.intel.driver import IntelQATDriver
from cyborg.tests import base
from cyborg.tests.unit.accelerator.drivers.qat.intel import prepare_test_data

import fixtures


class TestIntelQATDriver(base.TestCase):
    def setUp(self):
        super(TestIntelQATDriver, self).setUp()
        self.pcipath = sysinfo.PCI_DEVICES_PATH
        tmp_sys_dir = self.useFixture(fixtures.TempDir())
        prepare_test_data.create_fake_sysfs(tmp_sys_dir.path)
        tmp_path = tmp_sys_dir.path
        sysinfo.PCI_DEVICES_PATH = os.path.join(
            tmp_path, sysinfo.PCI_DEVICES_PATH.split("/", 1)[-1])

    def tearDown(self):
        super(TestIntelQATDriver, self).tearDown()
        sysinfo.PCI_DEVICES_PATH = self.pcipath

    def test_discover(self):
        attach_handle_list = [
            [
                {'attach_type': 'PCI',
                 'attach_info': '{"bus": "05", '
                                '"device": "01", '
                                '"domain": "0000", '
                                '"function": "0"}',
                 'in_use': False}
            ],
            [
                {'attach_type': 'PCI',
                 'attach_info': '{"bus": "06", '
                                '"device": "00", '
                                '"domain": "0000", '
                                '"function": "0"}',
                 'in_use': False}
            ]
        ]
        expected = [{'vendor': '0x8086',
                     'type': 'QAT',
                     'deployable_list':
                         [
                             {'num_accelerators': 1,
                              'name': '0000:05:01.0',
                              'attach_handle_list': attach_handle_list[0]
                              },
                         ],
                     'controlpath_id':
                         {
                             'cpid_info': '{"bus": "05", '
                                          '"device": "00", '
                                          '"domain": "0000", '
                                          '"function": "0"}',
                             'cpid_type': 'PCI'}
                     },
                    {'vendor': '0x8086',
                     'type': 'QAT',
                     'deployable_list':
                         [
                             {'num_accelerators': 1,
                              'name': '0000:06:00.0',
                              'attach_handle_list': attach_handle_list[1]
                              },
                         ],
                     'controlpath_id':
                         {
                             'cpid_info': '{"bus": "06", '
                                          '"device": "00", '
                                          '"domain": "0000", '
                                          '"function": "0"}',
                             'cpid_type': 'PCI'}
                     }
                    ]
        intel = IntelQATDriver()
        qats = intel.discover()
        list.sort(qats, key=lambda x: x._obj_deployable_list[0].name)
        self.assertEqual(2, len(qats))
        for i in range(len(qats)):
            qat_dict = qats[i].as_dict()
            qat_dep_list = qat_dict['deployable_list']
            qat_attach_handle_list = \
                qat_dep_list[0].as_dict()['attach_handle_list']
            self.assertEqual(expected[i]['vendor'], qat_dict['vendor'])
            self.assertEqual(expected[i]['controlpath_id'],
                             qat_dict['controlpath_id'])
            self.assertEqual(expected[i]['deployable_list'][0]
                             ['num_accelerators'],
                             qat_dep_list[0].as_dict()['num_accelerators'])
            self.assertEqual(1, len(qat_attach_handle_list))
            self.assertEqual(attach_handle_list[i][0],
                             qat_attach_handle_list[0].as_dict())
