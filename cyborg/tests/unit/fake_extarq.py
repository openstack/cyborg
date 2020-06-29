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
from cyborg.objects.extarq import fpga_ext_arq


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
        "device_profile_group": {
            "trait:CUSTOM_FPGA_INTEL": "required",
            "resources:FPGA": "1",
            "accel:bitstream_id": "b069d97a-010a-4057-b70d-eca2b337fc9c"}
    }
    dp_groups = [
        {"device_profile_group": {"resources:GPU": "1"}},
        {"device_profile_group": {
            "trait:CUSTOM_FPGA_INTEL": "required",
            "resources:FPGA": "1"}},
        {"device_profile_group": {
            "trait:CUSTOM_FPGA_INTEL": "required",
            "resources:FPGA": "1",
            "accel:bitstream_id": "b069d97a-010a-4057-b70d-eca2b337fc9c"}},
        {"device_profile_group": {
            "trait:CUSTOM_FPGA_INTEL": "required",
            "resources:FPGA": "1",
            "accel:function_id": "25453786-03e0-4ee7-a640-969eb5a5aa44"}},
        {"device_profile_group": {
            "trait:CUSTOM_FPGA_INTEL": "required",
            "resources:FPGA": "1",
            "accel:bitstream_id": "b069d97a-010a-4057-b70d-eca2b337fc9c",
            "accel:function_id": "25453786-03e0-4ee7-a640-969eb5a5aa44"}},
    ]
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
         "device_profile_group_id": 2,
         "device_rp_uuid": "a1ec17f2-0051-4737-bac4-f074d8a01a9c",
         },
        {"uuid": "3049ad04-a2b1-40a3-b9c8-480a5e661645",
         "device_profile_group_id": 3,
         "device_rp_uuid": "57455a49-bde4-490e-9179-9aa84a3870bb",
         },
        {"uuid": "3a9a07e7-d126-47a5-bf11-dcc04f9e60ff",
         "device_profile_group_id": 4,
         "device_rp_uuid": "fbd485e1-40b1-4a7e-84b9-f6b6959114a4",
         },
    ]
    new_arqs = []
    for idx, new_arq in enumerate(arqs):
        common.update(dp_groups[idx])
        new_arq.update(common)
        new_arq.update(id=idx)
        new_arqs.append(new_arq)
    return new_arqs


def _get_arqs_resloved_as_dict():
    arqs = [  # Corresponds to 1st device profile in fake_device)profile.py
        {"uuid": 'a097fefa-da62-4630-8e8b-424c0e3426dd',
         "device_profile_group_id": 0,
         "state": "Initial",
         "device_profile_name": "afaas_example_1",
         "device_rp_uuid": None,
         "hostname": None,
         "instance_uuid": None,
         "attach_handle_type": None,
         # attach_handle info should vary across ARQs but ignored for testing
         "attach_handle_info": {},
         "device_profile_group": {}
         },
        {"uuid": 'aa140114-4869-45ea-8213-45f530804b0e',
         "device_profile_group_id": 1,
         "device_rp_uuid": "fbd485e1-40b1-4a7e-84b9-f6b6959114a5",
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
         "device_profile_group": {
             "trait:CUSTOM_FPGA_INTEL": "required",
             "resources:FPGA": "1",
             "accel:bitstream_id": "b069d97a-010a-4057-b70d-eca2b337fc9c"}
         },
    ]
    new_arqs = []
    for idx, new_arq in enumerate(arqs):
        new_arq.update(id=idx)
        new_arqs.append(new_arq)
    return new_arqs


def _get_arqs_bind_as_dict():
    common = [
        {
            "state": "Bound",
            "device_profile_name": "afaas_example_1",
            "hostname": "myhost1",
            "instance_uuid": "5922a70f-1e06-4cfd-88dd-a332120d7144",
            "attach_handle_type": "PCI",
            # attach_handle info should vary across ARQs but ignored for
            # testing
            "attach_handle_info": {
                "bus": "1",
                "device": "0",
                "domain": "0",
                "function": "0"
            },
            "device_profile_group": {"resources:GPU": "1"}
        }, {
            "state": "Deleting",
            "device_profile_name": "afaas_example_2",
            "hostname": "myhost1",
            "instance_uuid": "5922a70f-1e06-4cfd-88dd-a332120d7144",
            "attach_handle_type": "PCI",
            # attach_handle info should vary across ARQs but ignored for
            # testing
            "attach_handle_info": {
                "bus": "2",
                "device": "0",
                "domain": "0",
                "function": "0"
            },
            "device_profile_group": {
                "trait:CUSTOM_FPGA_INTEL": "required",
                "resources:FPGA": "1"}
        }, {
            "state": "Deleting",
            "device_profile_name": "afaas_example_3",
            "hostname": "myhost3",
            "instance_uuid": "5922a70f-1e06-4cfd-88dd-a332120d7146",
            "attach_handle_type": "PCI",
            # attach_handle info should vary across ARQs but ignored for
            # testing
            "attach_handle_info": {
                "bus": "3",
                "device": "0",
                "domain": "0",
                "function": "0"
            },
            "device_profile_group": {
                "trait:CUSTOM_FPGA_INTEL": "required",
                "resources:FPGA": "1",
                "accel:bitstream_id": "b069d97a-010a-4057-b70d-eca2b337fc9e"}
        }, {
            "state": "Unbound",
            "device_profile_name": "afaas_example_2",
            "hostname": "myhost1",
            "instance_uuid": "5922a70f-1e06-4cfd-88dd-a332120d7144",
            "attach_handle_type": "PCI",
            # attach_handle info should vary across ARQs but ignored for
            # testing
            "attach_handle_info": {
                "bus": "2",
                "device": "0",
                "domain": "0",
                "function": "0"
            },
            "device_profile_group": {
                "trait:CUSTOM_FPGA_INTEL": "required",
                "resources:FPGA": "1"}
        },
    ]
    arqs = [  # Corresponds to 1st device profile in fake_device)profile.py
        {"uuid": "a097fefa-da62-4630-8e8b-424c0e3426de",
         "device_profile_group_id": 0,
         "device_rp_uuid": "8787595e-9954-49f8-b5c1-cdb55b59062e",
         },
        {"uuid": "aa140114-4869-45ea-8213-45f530804b0d",
         "device_profile_group_id": 0,
         "device_rp_uuid": "a1ec17f2-0051-4737-bac4-f074d8a01a9d",
         },
        {"uuid": "292b2fa2-0831-484c-aeac-09c794428a5e",
         "device_profile_group_id": 0,
         "device_rp_uuid": "57455a49-bde4-490e-9179-9aa84a3870bb",
         },
        {"uuid": "292b2fa2-0831-484c-aeac-09c794428a5d",
         "device_profile_group_id": 0,
         "device_rp_uuid": "57455a49-bde4-490e-9179-9aa84a3870bc",
         }
    ]
    new_arqs = []
    for idx, new_arq in enumerate(arqs):
        new_arq.update(common[idx])
        new_arq.update(id=idx)
        new_arqs.append(new_arq)
    return new_arqs


def _convert_from_dict_to_obj(arq_dict):
    obj_arq = arq.ARQ()
    for field in arq_dict.keys():
        obj_arq[field] = arq_dict[field]
    obj_extarq = ext_arq.ExtARQ()
    obj_extarq.arq = obj_arq
    obj_extarq.device_profile_group = arq_dict["device_profile_group"]
    return obj_extarq


def get_fake_extarq_objs():
    arq_list = _get_arqs_as_dict()
    obj_extarqs = list(map(_convert_from_dict_to_obj, arq_list))
    return obj_extarqs


def get_fake_extarq_resolved_objs():
    arq_list = _get_arqs_resloved_as_dict()
    obj_extarqs = list(map(_convert_from_dict_to_obj, arq_list))
    return obj_extarqs


def get_fake_extarq_bind_objs():
    arq_list = _get_arqs_bind_as_dict()
    obj_extarqs = list(map(_convert_from_dict_to_obj, arq_list))
    return obj_extarqs


def _convert_from_dict_to_fpga_obj(arq_dict):
    obj_arq = arq.ARQ()
    for field in arq_dict.keys():
        obj_arq[field] = arq_dict[field]
    obj_extarq = fpga_ext_arq.FPGAExtARQ()
    obj_extarq.arq = obj_arq
    obj_extarq.device_profile_group = arq_dict["device_profile_group"]
    return obj_extarq


def get_fake_fpga_extarq_objs():
    arq_list = _get_arqs_as_dict()[1:]
    obj_extarqs = list(map(_convert_from_dict_to_fpga_obj, arq_list))
    return obj_extarqs


def get_fake_db_extarqs():
    db_extarqs = []
    for db_extarq in _get_arqs_as_dict():
        db_extarq.update({'device_profile_id': 0})
        db_extarqs.append(db_extarq)
    return db_extarqs


def get_fake_fpga_db_extarqs():
    return get_fake_db_extarqs()[1:]


def get_patch_list(same_device=True):
    """Returns a list of bindings for many ARQs.

    :param same_device: Flag that the returned bindings for all ARQs
        must be for the same device.
    """
    arqs = _get_arqs_as_dict()
    host_binding = {'path': '/hostname', 'op': 'add',
                    'value': arqs[0]['hostname']}
    inst_binding = {'path': '/instance_uuid', 'op': 'add',
                    'value': arqs[0]['instance_uuid']}
    device_rp_uuid = 'fb16c293-5739-4c84-8590-926f9ab16669'
    patch_list = {}
    for newarq in arqs:
        dev_uuid = device_rp_uuid if same_device else newarq['device_rp_uuid']
        dev_binding = {'path': '/device_rp_uuid', 'op': 'add',
                       'value': dev_uuid}
        patch_list[newarq['uuid']] = [host_binding, inst_binding, dev_binding]
    return patch_list, device_rp_uuid
