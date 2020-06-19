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

import json
from unittest import mock

from cyborg.accelerator.drivers.aichip.huawei.ascend import AscendDriver
from cyborg.tests import base

d100_pci_res = (
    '0000:00:0c.0 Processing accelerators [1200]:'
    ' Device [19e5:d100] (rev 20)\n'
    '0000:00:0d.0 Processing accelerators [1200]:'
    ' Device [19e5:d100] (rev 20)\n',)


class TestAscendDriver(base.TestCase):

    @mock.patch('cyborg.accelerator.drivers.aichip.'
                'huawei.ascend.lspci_privileged',
                return_value=d100_pci_res)
    def test_discover(self, mock_pci):
        ascend_driver = AscendDriver()
        npu_list = ascend_driver.discover()
        self.assertEqual(2, len(npu_list))
        for ascend in npu_list:
            self.assertEqual('AICHIP', ascend.type)
            self.assertEqual('PCI', ascend.controlpath_id.cpid_type)
            self.assertEqual(json.loads(
                '{"class": "Processing accelerators", "device_id": "d100"}'),
                json.loads(ascend.std_board_info))
            self.assertEqual('19e5', ascend.vendor)

        self.assertEqual(
            {"device": "0c", "bus": "00", "domain": "0000", "function": "0"},
            json.loads(npu_list[0].controlpath_id.cpid_info))
        self.assertEqual(
            {"device": "0d", "bus": "00", "domain": "0000", "function": "0"},
            json.loads(npu_list[1].controlpath_id.cpid_info))

        self.assertEqual('Device_0000_00_0c_0',
                         npu_list[0].deployable_list[0].name)
        self.assertEqual('Device_0000_00_0d_0',
                         npu_list[1].deployable_list[0].name)
