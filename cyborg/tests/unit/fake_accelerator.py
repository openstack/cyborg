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


def fake_db_accelerator(**updates):
    db_accelerator = {
        'id': 1,
        'deleted': False,
        'uuid': uuidutils.generate_uuid(),
        'name': 'fake-name',
        'description': 'fake-desc',
        'project_id': 'fake-pid',
        'user_id': 'fake-uid',
        'device_type': 'fake-dtype',
        'acc_type': 'fake-acc_type',
        'acc_capability': 'fake-cap',
        'vendor_id': 'fake-vid',
        'product_id': 'fake-pid',
        'remotable': 0
        }

    for name, field in objects.Accelerator.fields.items():
        if name in db_accelerator:
            continue
        if field.nullable:
            db_accelerator[name] = None
        elif field.default != fields.UnspecifiedDefault:
            db_accelerator[name] = field.default
        else:
            raise Exception('fake_db_accelerator needs help with %s' % name)

    if updates:
        db_accelerator.update(updates)

    return db_accelerator


def fake_accelerator_obj(context, obj_accelerator_class=None, **updates):
    if obj_accelerator_class is None:
        obj_accelerator_class = objects.Accelerator
    expected_attrs = updates.pop('expected_attrs', None)
    acc = obj_instance_class._from_db_object(context,
                                             obj_instance_class(),
                                             fake_db_instance(**updates),
                                             expected_attrs=expected_attrs)
    acc.obj_reset_changes()
    return acc
