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


def fake_db_attribute(**updates):
    attr_uuid = uuidutils.generate_uuid()
    db_attribute = {
        'id': 0,
        'uuid': attr_uuid,
        'deployable_id': 1,
        'key': 'rc',
        'value': 'FPGA'
        }

    for name, field in objects.Attribute.fields.items():
        if name in db_attribute:
            continue
        if field.nullable:
            db_attribute[name] = None
        elif field.default != fields.UnspecifiedDefault:
            db_attribute[name] = field.default
        else:
            raise Exception('fake_db_attribute needs help with %s' % name)

    if updates:
        db_attribute.update(updates)

    return db_attribute


def fake_attribute_obj(context, obj_attr_class=None, **updates):
    if obj_attr_class is None:
        obj_attr_class = objects.Attribute
    attribute = obj_attr_class._from_db_object(
        obj_attr_class(),
        fake_db_attribute(**updates))
    attribute.obj_reset_changes()
    return attribute
