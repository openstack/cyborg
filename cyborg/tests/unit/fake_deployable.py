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


def fake_db_deployable(**updates):
    root_uuid = uuidutils.generate_uuid()
    db_deployable = {
        'id': 1,
        'uuid': root_uuid,
        'name': 'dp_name',
        'parent_id': None,
        'root_id': 1,
        'num_accelerators': 4,
        'device_id': 0,
        'driver_name': "fake-driver-name",
        'rp_uuid': None,
        'bitstream_id': None,
        }

    for name, field in objects.Deployable.fields.items():
        if name in db_deployable:
            continue
        if field.nullable:
            db_deployable[name] = None
        elif field.default != fields.UnspecifiedDefault:
            db_deployable[name] = field.default
        else:
            raise Exception('fake_db_deployable needs help with %s' % name)

    if updates:
        db_deployable.update(updates)

    return db_deployable


def fake_deployable_obj(context, obj_dpl_class=None, **updates):
    if obj_dpl_class is None:
        obj_dpl_class = objects.Deployable
    deploy = obj_dpl_class._from_db_object(obj_dpl_class(),
                                           fake_db_deployable(**updates))
    deploy.obj_reset_changes()
    return deploy
