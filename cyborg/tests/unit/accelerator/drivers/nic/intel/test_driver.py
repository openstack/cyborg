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
from unittest import mock

from cyborg.accelerator.drivers.nic.intel import sysinfo

from cyborg.accelerator.drivers.nic.intel.driver import IntelNICDriver
from cyborg.tests import base
from cyborg.tests.unit.accelerator.drivers.nic.intel import prepare_test_data

import fixtures


class TestIntelNICDriver(base.TestCase):
    def setUp(self):
        super(TestIntelNICDriver, self).setUp()
        self.pcipath = sysinfo.PCI_DEVICES_PATH_PATTERN
        tmp_sys_dir = self.useFixture(fixtures.TempDir())
        prepare_test_data.create_fake_sysfs(tmp_sys_dir.path)
        tmp_path = tmp_sys_dir.path
        sysinfo.PCI_DEVICES_PATH_PATTERN = os.path.join(
            tmp_path, sysinfo.PCI_DEVICES_PATH_PATTERN.split("/", 1)[-1])

    def tearDown(self):
        super(TestIntelNICDriver, self).tearDown()
        sysinfo.PCI_DEVICES_PATH = self.pcipath

    @mock.patch("cyborg.accelerator.common.utils.get_ifname_by_pci_address")
    def test_discover(self, mock_device_ifname):
        mock_device_ifname.return_value = "ethx"
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
        attribute_list = [
            [
                {
                    "key": "rc",
                    "value": "CUSTOM_NIC"
                    },
                {
                    "key": "trait0",
                    "value": "CUSTOM_VF"
                    }
            ],
            [
                {
                    "key": "rc",
                    "value": "CUSTOM_NIC"
                    },
                {
                    "key": "trait0",
                    "value": "CUSTOM_PF"
                    }
            ],
        ]
        expected = [{'vendor': '0x8086',
                     'type': 'NIC',
                     'deployable_list':
                         [
                             {'num_accelerators': 1,
                              'name': '0000:05:01.0',
                              'attach_handle_list': attach_handle_list[0],
                              'attribute_list':attribute_list[0]
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
                     'type': 'NIC',
                     'deployable_list':
                         [
                             {'num_accelerators': 1,
                              'name': '0000:06:00.0',
                              'attach_handle_list': attach_handle_list[1],
                              'attribute_list':attribute_list[1]
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
        intel = IntelNICDriver()
        nics = intel.discover()
        list.sort(nics, key=lambda x: x._obj_deployable_list[0].name)
        self.assertEqual(2, len(nics))
        for i in range(len(nics)):
            nic_dict = nics[i].as_dict()
            nic_dep_list = nic_dict['deployable_list']
            nic_attach_handle_list = \
                nic_dep_list[0].as_dict()['attach_handle_list']
            nic_attribute_list = \
                nic_dep_list[0].as_dict()['attribute_list']
            self.assertEqual(expected[i]['vendor'], nic_dict['vendor'])
            self.assertEqual(expected[i]['controlpath_id'],
                             nic_dict['controlpath_id'])
            self.assertEqual(expected[i]['deployable_list'][0]
                             ['num_accelerators'],
                             nic_dep_list[0].as_dict()['num_accelerators'])
            self.assertEqual(1, len(nic_attach_handle_list))
            self.assertEqual(attach_handle_list[i][0],
                             nic_attach_handle_list[0].as_dict())
            self.assertEqual(attribute_list[i][0],
                             nic_attribute_list[0].as_dict())
