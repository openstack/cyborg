# Copyright 2019 Intel Inc.
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

from cyborg.objects import arq
from cyborg.objects import ext_arq


def _get_arqs_as_dict():
    common = {
        "state": "Bound",
        "device_profile_name": "afaas_example_1",
        "hostname": "myhost",
        "instance_uuid": "5922a70f-1e06-4cfd-88dd-a332120d7144",
        "attach_handle_type": "PCI",
        # attach_handle info should vary across ARQs but ignored for testing
        "attach_handle_info": {
            "bus": "1",
            "device": "0",
            "domain": "0",
            "function": "0"
        },
    }
    arqs = [  # Corresponds to 1st device profile in fake_device)profile.py
        {"uuid": "a097fefa-da62-4630-8e8b-424c0e3426dc",
         "device_profile_group_id": 0,
         "device_rp_uuid": "8787595e-9954-49f8-b5c1-cdb55b59062f",
         },
        {"uuid": "aa140114-4869-45ea-8213-45f530804b0f",
         "device_profile_group_id": 1,
         "device_rp_uuid": "a1ec17f2-0051-4737-bac4-f074d8a01a9c",
         },
        {"uuid": "292b2fa2-0831-484c-aeac-09c794428a5d",
         "device_profile_group_id": 1,
         "device_rp_uuid": "a1ec17f2-0051-4737-bac4-f074d8a01a9c",
         },
    ]
    new_arqs = []
    for idx, new_arq in enumerate(arqs):
        new_arq.update(common)
        new_arq.update(id=idx)
        new_arqs.append(new_arq)
    return new_arqs


def _convert_from_dict_to_obj(arq_dict):
    obj_arq = arq.ARQ()
    for field in arq_dict.keys():
        obj_arq[field] = arq_dict[field]
    obj_extarq = ext_arq.ExtARQ()
    obj_extarq.arq = obj_arq
    return obj_extarq


def get_fake_extarq_objs():
    arq_list = _get_arqs_as_dict()
    obj_extarqs = list(map(_convert_from_dict_to_obj, arq_list))
    return obj_extarqs


def get_fake_db_extarqs():
    db_extarqs = []
    for db_extarq in _get_arqs_as_dict():
        db_extarq.update({'device_profile_id': 0})
        db_extarqs.append(db_extarq)
    return db_extarqs
