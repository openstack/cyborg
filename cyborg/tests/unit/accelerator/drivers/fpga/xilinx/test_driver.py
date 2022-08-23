# Copyright 2021 Inspur, Inc.
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
from unittest import mock

from cyborg.accelerator.drivers.fpga.xilinx.driver import XilinxFPGADriver
from cyborg.tests import base

XILINX_FPGA_INFO = ["0000:3b:00.0 Processing accelerators [1200]: "
                    "Xilinx Corporation Device [10ee:5000]\n"
                    "0000:3b:00.1 Processing accelerators [1200]: "
                    "Xilinx Corporation Device [10ee:5001]"]


def fake_output(arg):
    if arg == ['lspci', '-nnn', '-D']:
        return XILINX_FPGA_INFO


class TestXilinxFPGADriver(base.TestCase):

    def setUp(self):
        super(TestXilinxFPGADriver, self).setUp()

    @mock.patch('cyborg.accelerator.drivers.fpga.'
                'xilinx.sysinfo.lspci_privileged')
    def test_discover(self, mock_devices_for_vendor):
        mock_devices_for_vendor.side_effect = fake_output
        self.set_defaults(host='fake-host', debug=True)
        fpga_list = XilinxFPGADriver().discover()
        self.assertEqual(1, len(fpga_list))
        attach_handle_list = [
            {'attach_type': 'PCI',
             'attach_info': '{"bus": "3b", '
                            '"device": "00", '
                            '"domain": "0000", '
                            '"function": "0"}',
             'in_use': False},
            {'attach_type': 'PCI',
             'attach_info': '{"bus": "3b", '
                            '"device": "00", '
                            '"domain": "0000", '
                            '"function": "1"}',
             'in_use': False}
        ]
        attribute_list = [
            {'key': 'rc', 'value': 'FPGA'},
            {'key': 'trait0', 'value': 'CUSTOM_FPGA_XILINX'},
            {'key': 'trait1', 'value': 'CUSTOM_FPGA_PRODUCT_ID_5000'},
        ]
        expected = {
            'vendor': '10ee',
            'type': 'FPGA',
            'std_board_info': {"controller": "Processing accelerators",
                               "product_id": "5000"},
            'vendor_board_info': {"vendor_info": "fpga_vb_info"},
            'deployable_list':
                [
                    {
                        'num_accelerators': 1,
                        'driver_name': 'XILINX',
                        'name': 'fake-host_0000:3b:00.0',
                        'attach_handle_list': attach_handle_list,
                        'attribute_list': attribute_list
                    },
                ],
            'controlpath_id': {'cpid_info': '{"bus": "3b", '
                                            '"device": "00", '
                                            '"domain": "0000", '
                                            '"function": "0"}',
                               'cpid_type': 'PCI'}
        }
        fpga_obj = fpga_list[0]
        fpga_dict = fpga_obj.as_dict()
        fpga_dep_list = fpga_dict['deployable_list']
        fpga_attach_handle_list = (
            fpga_dep_list[0].as_dict()['attach_handle_list'])
        fpga_attribute_list = fpga_dep_list[0].as_dict()['attribute_list']
        attri_obj_data = []
        [attri_obj_data.append(attr.as_dict()) for attr in fpga_attribute_list]
        attribute_actual_data = sorted(attri_obj_data, key=lambda i: i['key'])
        self.assertEqual(expected['vendor'], fpga_dict['vendor'])
        self.assertEqual(expected['controlpath_id'],
                         fpga_dict['controlpath_id'])
        self.assertEqual(expected['std_board_info'],
                         jsonutils.loads(fpga_dict['std_board_info']))
        self.assertEqual(expected['vendor_board_info'],
                         jsonutils.loads(fpga_dict['vendor_board_info']))
        self.assertEqual(expected['deployable_list'][0]['num_accelerators'],
                         fpga_dep_list[0].as_dict()['num_accelerators'])
        self.assertEqual(expected['deployable_list'][0]['name'],
                         fpga_dep_list[0].as_dict()['name'])
        self.assertEqual(expected['deployable_list'][0]['driver_name'],
                         fpga_dep_list[0].as_dict()['driver_name'])
        self.assertEqual(2, len(fpga_attach_handle_list))
        self.assertEqual(attach_handle_list[0],
                         fpga_attach_handle_list[0].as_dict())
        self.assertEqual(attach_handle_list[1],
                         fpga_attach_handle_list[1].as_dict())
        self.assertEqual(attribute_list, attribute_actual_data)

    @mock.patch('cyborg.accelerator.drivers.fpga.xilinx.driver.'
                '_fpga_program_privileged')
    def test_program(self, mock_prog):
        bdf = '0000:3b:00:0'
        expect_cmd_args = ['program', '--device', bdf, '--base',
                           '--image', '/path/image']

        xilinx_driver = XilinxFPGADriver()
        cpid_info = {"domain": "0000", "bus": "3b",
                     "device": "00", "function": "0"}
        cpid = {'cpid_type': 'PCI', 'cpid_info': cpid_info}

        # program PF
        mock_prog.return_value = bytes([0])
        xilinx_driver.program(cpid, "/path/image")
        mock_prog.assert_called_with(expect_cmd_args)
