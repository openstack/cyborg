# Copyright 2017 Huawei Technologies Co.,LTD.
# All Rights Reserved.
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

"""Cyborg db test utilities."""


def get_test_accelerator(**kw):
    return {
        'name': kw.get('name', 'name'),
        'description': kw.get('description', 'description'),
        'device_type': kw.get('device_type', 'device_type'),
        'acc_type': kw.get('acc_type', 'acc_type'),
        'acc_capability': kw.get('acc_capability', 'acc_capability'),
        'vendor_id': kw.get('vendor_id', 'vendor_id'),
        'product_id': kw.get('product_id', 'product_id'),
        'remotable': kw.get('remotable', 1),
        'project_id': kw.get('project_id', 'b492a6fb12964ae3bd291ce585107d48'),
        'user_id': kw.get('user_id', '7009409e21614d1db1ef7a8c5ee101d8'),
    }


def get_test_deployable(**kw):
    return {
        'id': kw.get('id', 1),
        'uuid': kw.get('uuid', '10efe63d-dfea-4a37-ad94-4116fba5011'),
        'parent_id': kw.get('parent_id', None),
        'root_id': kw.get('root_id', 0),
        'name': kw.get('name', 'name'),
        'num_accelerators': kw.get('num_accelerators', 4),
        'device_id': kw.get('device_id', 0),
        'created_at': kw.get('created_at', None),
        'updated_at': kw.get('updated_at', None)
    }


def get_test_extarq(**kwargs):
    return {
        'uuid': kwargs.get('uuid', '10efe63d-dfea-4a37-ad94-4116fba5098'),
        'id': kwargs.get('id', 1),
        'state': kwargs.get('state', 'bound'),
        'device_profile_id': kwargs.get('id', 1),
        'hostname': kwargs.get('hostname', 'testnode1'),
        'device_rp_uuid': kwargs.get('device_rp_uuid',
                                     'f2b96c5f-242a-41a0-a736-b6e1fada071b'),
        'device_instance_uuid':
            kwargs.get('device_rp_uuid',
                       '6219e0fb-2935-4db2-a3c7-86a2ac3ac84e'),
        'attach_handle_id': kwargs.get('id', 1),
        'created_at': kwargs.get('created_at', None),
        'updated_at': kwargs.get('updated_at', None)
    }


def get_test_arq(**kwargs):
    return {
        'uuid': kwargs.get('uuid', '10efe63d-dfea-4a37-ad94-4116fba5098'),
        'id': kwargs.get('id', 1),
        'state': kwargs.get('state', 'Initial'),
        'device_profile': kwargs.get('device_profile', None),
        'hostname': kwargs.get('hostname', 'testnode1'),
        'device_rp_uuid': kwargs.get('device_rp_uuid',
                                     'f2b96c5f-242a-41a0-a736-b6e1fada071b'),
        'device_instance_uuid':
            kwargs.get('device_rp_uuid',
                       '6219e0fb-2935-4db2-a3c7-86a2ac3ac84e'),
        'attach_handle': kwargs.get('attach_handle', None),
        'created_at': kwargs.get('created_at', None),
        'updated_at': kwargs.get('updated_at', None),
        'substate': kwargs.get('substate', 'Initial'),
    }


def get_test_attach_handle(**kw):
    return {
        'uuid': kw.get('uuid', '10efe63d-dfea-4a37-ad94-4116fba5098'),
        'id': kw.get('id', 1),
        'deployable_id': kw.get('deployable_id', 1),
        'cpid_id': kw.get('cpid_id', 1),
        'in_use': kw.get('in_use', False),
        'attach_type': kw.get('attach_type', "PCI"),
        'attach_info': kw.get('attach_info', "attach_info"),
        'created_at': kw.get('create_at', None),
        'updated_at': kw.get('updated_at', None),
    }


def get_test_control_path(**kw):
    return {
        'uuid': kw.get('uuid', '10efe63d-dfea-4a37-ad94-4116fba5098'),
        'id': kw.get('id', 1),
        'device_id': kw.get('device_id', 1),
        'cpid_type': kw.get('cpid_type', "PCI"),
        'cpid_info': kw.get('cpid_info', "cpid_info"),
        'created_at': kw.get('create_at', None),
        'updated_at': kw.get('updated_at', None),
    }


def get_test_device(**kw):
    return {
        'id': kw.get('id', 1),
        'uuid': kw.get('uuid', '83f92afa-1aa8-4548-a3a3-d218ff71d768'),
        'type': kw.get('type', 'FPGA'),
        'vendor': kw.get('vendor', 'Intel'),
        # FIXME(Yumeng) should give details of std_board_info,
        # vendor_board_info examples once they are determined.
        'model': kw.get('model', 'PAC Arria 10'),
        'std_board_info': kw.get('std_board_info',
                                 'dictionary with standard fields'),
        'vendor_board_info': kw.get('vendor_board_info',
                                    'dictionary with vendor specific fields'),
        'hostname': kw.get('hostname', 'hostname'),
        'created_at': kw.get('create_at', None),
        'updated_at': kw.get('updated_at', None),
    }


def get_test_device_profile(**kw):
    return {
        'id': kw.get('id', 1),
        'uuid': kw.get('uuid', 'c0f43d55-03bf-4831-8639-9bbdb6be2478'),
        'name': kw.get('name', 'name'),
        'profile_json': kw.get(
            'profile_json',
            '{"version": "1.0", \
             "groups": [{"resources:CUSTOM_ACCELERATOR_FPGA": "1"}, \
             {"trait:CUSTOM_FPGA_INTEL_PAC_ARRIA10": "required"}, \
             {"trait:CUSTOM_FUNCTION_ID_3AFB": "required"}]}'),
        'created_at': kw.get('create_at', None),
        'updated_at': kw.get('updated_at', None),
    }
