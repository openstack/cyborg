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

from oslo_utils import uuidutils

from cyborg import objects
from cyborg.objects import fields
from cyborg.objects import virtual_function


def fake_db_virtual_function(**updates):
    root_uuid = uuidutils.generate_uuid()
    db_virtual_function = {
        'id': 1,
        'deleted': False,
        'uuid': root_uuid,
        'name': 'dp_name',
        'parent_uuid': None,
        'root_uuid': root_uuid,
        'address': '00:7f:bb.2',
        'host': 'host_name',
        'board': 'KU115',
        'vendor': 'Xilinx',
        'version': '1.0',
        'type': 'vf',
        'interface_type': 'pci',
        'assignable': True,
        'instance_uuid': None,
        'availability': 'Available',
        'accelerator_id': 1
        }

    for name, field in virtual_function.VirtualFunction.fields.items():
        if name in db_virtual_function:
            continue
        if field.nullable:
            db_virtual_function[name] = None
        elif field.default != fields.UnspecifiedDefault:
            db_virtual_function[name] = field.default
        else:
            raise Exception('fake_db_virtual_function needs help with %s'
                            % name)

    if updates:
        db_virtual_function.update(updates)

    return db_virtual_function


def fake_virtual_function_obj(context, obj_vf_class=None, **updates):
    if obj_vf_class is None:
        obj_vf_class = objects.VirtualFunction
    expected_attrs = updates.pop('expected_attrs', None)
    vf = obj_vf_class._from_db_object(context,
                                      obj_vf_class(),
                                      fake_db_virtual_function(**updates),
                                      expected_attrs=expected_attrs)
    vf.obj_reset_changes()
    return vf
