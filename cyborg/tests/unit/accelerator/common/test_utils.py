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


from cyborg.accelerator.common import utils
import unittest


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.utils = utils
        super(TestUtils, self).setUp()

    def test_pci_str_to_json(self):
        pci_address = '0000:0b:00.0'
        json_str = '{"bus": "0b", "device": "00", "domain": "0000", ' \
                   '"function": "0"}'
        result = self.utils.pci_str_to_json(pci_address)
        self.assertEqual(result, json_str)

        pci_address = '0000:0b:00.1'
        json_str = '{"bus": "0b", "device": "00", "domain": "0000", ' \
                   '"function": "1", "physical_network": "physnet"}'
        result = self.utils.pci_str_to_json(pci_address, 'physnet')
        self.assertEqual(result, json_str)

    def test_mdev_str_to_json(self):
        json_str = '{"asked_type": "type", "bus": "0b", "device": "00", ' \
                   '"domain": "0000", "function": "1", "vgpu_mark": "mask"}'
        result = self.utils.mdev_str_to_json('0000:0b:00.1', 'type', 'mask')
        self.assertEqual(result, json_str)

        json_str = '{"asked_type": null, "bus": "0b", "device": "00", ' \
                   '"domain": "0000", "function": "1", "vgpu_mark": null}'
        result = self.utils.mdev_str_to_json('0000:0b:00.1', None, None)
        self.assertEqual(result, json_str)

    def test_parse_address(self):
        result = self.utils.parse_address('0000:0b:00.1')
        self.assertEqual(result, ('0000', '0b', '00', '1'))
