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

import datetime

from oslo_serialization import jsonutils
from oslo_utils import uuidutils

from cyborg import objects
from cyborg.objects import fields


def fake_db_device(**updates):
    root_uuid = uuidutils.generate_uuid()
    db_device = {
        'id': 1,
        'uuid': root_uuid,
        'type': 'FPGA',
        'vendor': "vendor",
        'model': "model",
        'std_board_info': "std_board_info",
        'vendor_board_info': "vendor_board_info",
        'hostname': "hostname"
        }

    for name, field in objects.Device.fields.items():
        if name in db_device:
            continue
        if field.nullable:
            db_device[name] = None
        elif field.default != fields.UnspecifiedDefault:
            db_device[name] = field.default
        else:
            raise Exception('fake_db_device needs help with %s' % name)

    if updates:
        db_device.update(updates)

    return db_device


def fake_device_obj(context, obj_device_class=None, **updates):
    if obj_device_class is None:
        obj_device_class = objects.Device
    device = obj_device_class._from_db_object(obj_device_class(),
                                              fake_db_device(**updates))
    device.obj_reset_changes()
    return device
