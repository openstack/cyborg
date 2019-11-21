# Copyright 2018 Huawei Technologies Co.,LTD.
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

from cyborg import objects
from cyborg.objects import device
from cyborg.objects import fields


def get_fake_devices_as_dict():
    device1 = {
        "id": 1,
        "vendor": "0xABCD",
        "uuid": u"1c6c9033-560d-4a7a-bb8e-94455d1e7825",
        "hostname": "test-node-1",
        "vendor_board_info": "fake_vendor_info",
        "model": "miss model info",
        "type": "FPGA",
        "std_board_info": "{'class': 'Fake class', 'device_id': '0xabcd'}"
        }
    device2 = {
        "id": 2,
        "vendor": "0xDCBA",
        "uuid": u"1c6c9033-560d-4a7a-bb8e-94455d1e7826",
        "hostname": "test-node-2",
        "vendor_board_info": "fake_vendor_info",
        "model": "miss model info",
        "type": "GPU",
        "std_board_info": "{'class': 'Fake class', 'device_id': '0xdcba'}"
        }
    return [device1, device2]


def _convert_from_dict_to_obj(device_dict):
    obj_device = device.Device()
    for field in device_dict.keys():
        obj_device[field] = device_dict[field]
    return obj_device


def _convert_to_db_device(device_dict):
    for name, field in objects.Device.fields.items():
        if name in device_dict:
            continue
        if field.nullable:
            device_dict[name] = None
        elif field.default != fields.UnspecifiedDefault:
            device_dict[name] = field.default
        else:
            raise Exception('fake_db_device needs help with %s' % name)
    return device_dict


def get_db_devices():
    devices_list = get_fake_devices_as_dict()
    db_devices = list(map(_convert_to_db_device, devices_list))
    return db_devices


def get_fake_devices_objs():
    devices_list = get_fake_devices_as_dict()
    obj_devices = list(map(_convert_from_dict_to_obj, devices_list))
    return obj_devices
