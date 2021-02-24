# Copyright 2021 Inspur.
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
from cyborg.objects import attach_handle
from cyborg.objects import fields


def get_fake_attach_handle_as_dict():
    attach_handle1 = {
        'id': 1,
        'uuid': uuidutils.generate_uuid(),
        'in_use': 0,
        'cp_id': 1,
        'deployable_id': 1,
        'attach_type': "PCI",
        'attach_info': '{"domain": "0000", "bus": "0c",'
                       '"device": "0", "function": "1"}',
        }

    attach_handle2 = {
        'id': 2,
        'uuid': uuidutils.generate_uuid(),
        'in_use': 1,
        'cp_id': 2,
        'deployable_id': 2,
        'attach_type': "PCI",
        'attach_info': '{"domain": "0000", "bus": "0c",'
                       '"device": "0", "function": "1"}',
        }

    return [attach_handle1, attach_handle2]


def _convert_from_dict_to_obj(ah_dict):
    obj_ah = attach_handle.AttachHandle()
    for field in ah_dict.keys():
        obj_ah[field] = ah_dict[field]
    return obj_ah


def _convert_to_db_ah(ah_dict):
    for name, field in objects.AttachHandle.fields.items():
        if name in ah_dict:
            continue
        if field.nullable:
            ah_dict[name] = None
        elif field.default != fields.UnspecifiedDefault:
            ah_dict[name] = field.default
        else:
            raise Exception('fake_db_attach_handle needs help with %s' % name)
    return ah_dict


def get_db_attach_handles():
    ahs_list = get_fake_attach_handle_as_dict()
    db_ahs = list(map(_convert_to_db_ah, ahs_list))
    return db_ahs


def get_fake_attach_handle_objs():
    ahs_list = get_fake_attach_handle_as_dict()
    obj_ahs = list(map(_convert_from_dict_to_obj, ahs_list))
    return obj_ahs
