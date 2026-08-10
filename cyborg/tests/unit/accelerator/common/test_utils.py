# Copyright 2023 Inspur, Inc.
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


import unittest

from unittest import mock

from cyborg import privsep
from cyborg.accelerator.common import utils


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.utils = utils
        super().setUp()

    def test_pci_str_to_json(self):
        pci_address = '0000:0b:00.0'
        json_str = (
            '{"bus": "0b", "device": "00", "domain": "0000", "function": "0"}'
        )
        result = self.utils.pci_str_to_json(pci_address)
        self.assertEqual(result, json_str)

        pci_address = '0000:0b:00.1'
        json_str = (
            '{"bus": "0b", "device": "00", "domain": "0000", '
            '"function": "1", "physical_network": "physnet"}'
        )
        result = self.utils.pci_str_to_json(pci_address, 'physnet')
        self.assertEqual(result, json_str)

    def test_mdev_str_to_json(self):
        json_str = (
            '{"asked_type": "type", "bus": "0b", "device": "00", '
            '"domain": "0000", "function": "1", "vgpu_mark": "mask"}'
        )
        result = self.utils.mdev_str_to_json('0000:0b:00.1', 'type', 'mask')
        self.assertEqual(result, json_str)

        json_str = (
            '{"asked_type": null, "bus": "0b", "device": "00", '
            '"domain": "0000", "function": "1", "vgpu_mark": null}'
        )
        result = self.utils.mdev_str_to_json('0000:0b:00.1', None, None)
        self.assertEqual(result, json_str)

    def test_parse_address(self):
        result = self.utils.parse_address('0000:0b:00.1')
        self.assertEqual(result, ('0000', '0b', '00', '1'))

    def test_parse_lspci_line(self):
        line = (
            "0000:00:02.0 VGA compatible controller [0300]: "
            "Intel Corp Device [8086:1234] (rev 02)"
        )
        result = self.utils.parse_lspci_line(line)
        self.assertEqual(result["address"], "0000:00:02.0")
        self.assertEqual(result["class_name"], "VGA compatible controller")
        self.assertEqual(result["class_id"], "0300")
        self.assertEqual(result["device_name"], "Intel Corp Device")
        self.assertEqual(result["vendor_id"], "8086")
        self.assertEqual(result["device_id"], "1234")
        self.assertEqual(result["revision"], "02")
        self.assertEqual(result["raw_line"], line)

    def test_parse_lspci_line_normalizes_hex(self):
        line = "0000:3b:00.0 3D controller [0302]: NVIDIA [10DE:1DB4]"
        result = self.utils.parse_lspci_line(line)
        self.assertEqual(result["vendor_id"], "10de")
        self.assertEqual(result["device_id"], "1db4")

    def test_parse_lspci_line_no_match(self):
        self.assertIsNone(self.utils.parse_lspci_line("not a pci line"))

    @mock.patch('cyborg.accelerator.common.utils.lspci_privileged')
    def test_get_pci_devices(self, mock_lspci):
        mock_lspci.return_value = (
            "0000:00:02.0 VGA compatible controller [0300]: "
            "Intel [8086:1234]\n"
            "0000:3b:00.0 3D controller [0302]: NVIDIA [10de:1db4]\n"
            "a line that does not match the pattern"
        )
        result = list(self.utils.get_pci_devices())
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["vendor_id"], "8086")
        self.assertEqual(result[1]["device_id"], "1db4")
        for dev in result:
            self.assertIn("raw_line", dev)

    @mock.patch("cyborg.accelerator.common.utils.processutils.execute")
    def test_pci_details(self, mock_execute):
        mock_execute.return_value = ("driver info", "")
        privsep.sys_admin_pctxt.set_client_mode(False)
        self.addCleanup(privsep.sys_admin_pctxt.set_client_mode, True)
        result = self.utils.pci_details("0000:0b:00.0")
        mock_execute.assert_called_once_with(
            "lspci", "-k", "-s", "0000:0b:00.0"
        )
        self.assertEqual(result, "driver info")
