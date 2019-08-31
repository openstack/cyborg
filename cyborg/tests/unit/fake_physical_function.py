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
from cyborg.objects import physical_function


def fake_db_physical_function(**updates):
    root_uuid = uuidutils.generate_uuid()
    db_physical_function = {
        'id': 1,
        'deleted': False,
        'uuid': root_uuid,
        'name': 'dp_name',
        'parent_uuid': None,
        'root_uuid': root_uuid,
        'address': '00:7f:0b.2',
        'host': 'host_name',
        'board': 'KU115',
        'vendor': 'Xilinx',
        'version': '1.0',
        'type': 'pf',
        'interface_type': 'pci',
        'assignable': True,
        'instance_uuid': None,
        'availability': 'Available',
        'accelerator_id': 1
        }

    for name, field in physical_function.PhysicalFunction.fields.items():
        if name in db_physical_function:
            continue
        if field.nullable:
            db_physical_function[name] = None
        elif field.default != fields.UnspecifiedDefault:
            db_physical_function[name] = field.default
        else:
            raise Exception('fake_db_physical_function needs help with %s'
                            % name)

    if updates:
        db_physical_function.update(updates)

    return db_physical_function


def fake_physical_function_obj(context, obj_pf_class=None, **updates):
    if obj_pf_class is None:
        obj_pf_class = objects.VirtualFunction
    expected_attrs = updates.pop('expected_attrs', None)
    pf = obj_pf_class._from_db_object(context,
                                      obj_pf_class(),
                                      fake_db_physical_function(**updates),
                                      expected_attrs=expected_attrs)
    pf.obj_reset_changes()
    return pf
