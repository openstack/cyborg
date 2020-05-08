# Copyright 2020 Inspur Electronic Information Industry Co.,LTD.
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

from unittest import mock

from oslo_serialization import jsonutils

from cyborg.accelerator.drivers.ssd.base import SSDDriver
from cyborg.accelerator.drivers.ssd.inspur.driver import InspurNVMeSSDDriver
from cyborg.accelerator.drivers.ssd import utils
from cyborg.tests import base

NVME_SSD_INFO = \
    "0000:db:00.0 Non-Volatile memory controller [0108]: Inspur " \
    "Electronic Information Industry Co., Ltd. Device [1bd4:1001]" \
    " (rev 02)\n0000:db:01.0 Non-Volatile memory controller " \
    "[0108]: Inspur Electronic Information Industry Co., Ltd. " \
    "Device [1bd4:1001] (rev 02)"


class stdout(object):
    def readlines(self):
        return [NVME_SSD_INFO]


class p(object):
    def __init__(self):
        self.stdout = stdout()

    def wait(self):
        pass


class TestSSDDriverUtils(base.TestCase):

    def setUp(self):
        super().setUp()
        self.p = p()

    @mock.patch('cyborg.accelerator.drivers.ssd.utils.lspci_privileged')
    def test_discover_vendors(self, mock_devices):
        mock_devices.return_value = self.p.stdout.readlines()
        ssd_vendors = utils.discover_vendors()
        self.assertEqual(1, len(ssd_vendors))

    @mock.patch('cyborg.accelerator.drivers.ssd.utils.lspci_privileged')
    def test_discover_with_inspur_ssd_driver(self, mock_devices_for_vendor):
        mock_devices_for_vendor.return_value = self.p.stdout.readlines()
        self.set_defaults(host='host-192-168-32-195', debug=True)
        vendor_id = '1bd4'
        ssd_list = InspurNVMeSSDDriver.discover(vendor_id)
        self.assertEqual(2, len(ssd_list))
        attach_handle_list = [
            {'attach_type': 'PCI',
             'attach_info': '{"bus": "db", '
                            '"device": "00", '
                            '"domain": "0000", '
                            '"function": "0"}',
             'in_use': False}
        ]
        attribute_list = [
            {'key': 'rc', 'value': 'CUSTOM_SSD'},
            {'key': 'trait0', 'value': 'CUSTOM_SSD_INSPUR'},
            {'key': 'trait1', 'value': 'CUSTOM_SSD_PRODUCT_ID_1001'},
        ]
        expected = {
            'vendor': '1bd4',
            'type': 'SSD',
            'std_board_info':
                {"controller": "Non-Volatile memory controller",
                 "product_id": "1001"},
            'vendor_board_info': {"vendor_info": "ssd_vb_info"},
            'deployable_list':
                [
                    {
                        'num_accelerators': 1,
                        'driver_name': 'INSPUR',
                        'name': 'host-192-168-32-195_0000:db:00.0',
                        'attach_handle_list': attach_handle_list,
                        'attribute_list': attribute_list
                    },
                ],
            'controlpath_id': {'cpid_info': '{"bus": "db", '
                                            '"device": "00", '
                                            '"domain": "0000", '
                                            '"function": "0"}',
                               'cpid_type': 'PCI'}
        }
        ssd_obj = ssd_list[0]
        ssd_dict = ssd_obj.as_dict()
        ssd_dep_list = ssd_dict['deployable_list']
        ssd_attach_handle_list = \
            ssd_dep_list[0].as_dict()['attach_handle_list']
        ssd_attribute_list = \
            ssd_dep_list[0].as_dict()['attribute_list']
        attri_obj_data = []
        [attri_obj_data.append(attr.as_dict()) for attr in ssd_attribute_list]
        attribute_actual_data = sorted(attri_obj_data, key=lambda i: i['key'])
        self.assertEqual(expected['vendor'], ssd_dict['vendor'])
        self.assertEqual(expected['controlpath_id'],
                         ssd_dict['controlpath_id'])
        self.assertEqual(expected['std_board_info'],
                         jsonutils.loads(ssd_dict['std_board_info']))
        self.assertEqual(expected['vendor_board_info'],
                         jsonutils.loads(ssd_dict['vendor_board_info']))
        self.assertEqual(expected['deployable_list'][0]['num_accelerators'],
                         ssd_dep_list[0].as_dict()['num_accelerators'])
        self.assertEqual(expected['deployable_list'][0]['name'],
                         ssd_dep_list[0].as_dict()['name'])
        self.assertEqual(expected['deployable_list'][0]['driver_name'],
                         ssd_dep_list[0].as_dict()['driver_name'])
        self.assertEqual(attach_handle_list[0],
                         ssd_attach_handle_list[0].as_dict())
        self.assertEqual(attribute_list, attribute_actual_data)

    @mock.patch('cyborg.accelerator.drivers.ssd.utils.lspci_privileged')
    def test_discover_with_base_ssd_driver(self, mock_devices_for_vendor):
        mock_devices_for_vendor.return_value = self.p.stdout.readlines()
        with self.assertLogs(None, level='INFO') as cm:
            d = SSDDriver.create()
            ssd_list = d.discover()
        self.assertEqual(cm.output,
                         ['INFO:cyborg.accelerator.drivers.ssd.base:The '
                          'method "discover" is called in generic.SSDDriver'])
        self.assertEqual(2, len(ssd_list))
        self.assertEqual("1bd4", ssd_list[1].as_dict()['vendor'])
