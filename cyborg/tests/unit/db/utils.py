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

from cyborg.db import api as db_api


def get_test_deployable(**kw):
    return {
        'id': kw.get('id', 1),
        'uuid': kw.get('uuid', '10efe63d-dfea-4a37-ad94-4116fba50112'),
        'parent_id': kw.get('parent_id', None),
        'root_id': kw.get('root_id', 0),
        'name': kw.get('name', 'name'),
        'num_accelerators': kw.get('num_accelerators', 4),
        'device_id': kw.get('device_id', 0),
        'driver_name': kw.get('driver_name', 'NVIDIA'),
        'rp_uuid': kw.get('rp_uuid', '1c559644-2b56-3470-8427-d9d71f0f8621'),
        'bitstream_id': kw.get('bitstream_id', None),
        'created_at': kw.get('created_at', None),
        'updated_at': kw.get('updated_at', None)
    }


def create_test_deployable(context, **kwargs):
    """Create test deployable entry in DB and return Deployable DB object.

    Function to be used to create test Deployable objects in the database.
    :param context: request context.
    :param kwargs: kwargs which override default deployable attributes.
    :returns: Test Deployable DB object.
    """
    deployable = get_test_deployable(**kwargs)
    dbapi = db_api.get_instance()
    return dbapi.deployable_create(context, deployable)


def get_test_device(**kw):
    std_board_info = {
        "class": "Fake class",
        "device_id": "0xabcd"
        }
    return {
        'id': kw.get('id', 1),
        'uuid': kw.get('uuid', '20efe63d-dfea-4a37-ad94-4116fba50122'),
        'type': kw.get('type', "FPGA"),
        'vendor': kw.get('vendor', "0xABCD"),
        'model': kw.get('model', 'miss model info'),
        'std_board_info': kw.get('std_board_info', str(std_board_info)),
        'vendor_board_info': kw.get('vendor_board_info', 'fake_vendor_info'),
        'hostname': kw.get('hostname', "localhost"),
        'created_at': kw.get('created_at', None),
        'updated_at': kw.get('updated_at', None),
    }


def create_test_device(context, **kwargs):
    """Create test device entry in DB and return Device DB object.

    Function to be used to create test Device objects in the database.
    :param context: request context.
    :param kwargs: kwargs which override default device attributes.
    :returns: Test Device DB object.
    """
    device = get_test_device(**kwargs)
    dbapi = db_api.get_instance()
    return dbapi.device_create(context, device)


def get_test_extarq(**kwargs):
    return {
        'uuid': kwargs.get('uuid', '10efe63d-dfea-4a37-ad94-4116fba50986'),
        'id': kwargs.get('id', 1),
        'state': kwargs.get('state', 'Bound'),
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


def create_test_extarq(context, **kwargs):
    """Create test extend arq entry in DB and return ExtArq DB object.

    Function to be used to create test ExtArq objects in the database.
    :param context: request context.
    :param kwargs: kwargs which override default extend arq attributes.
    :returns: Test ExtArq DB object.
    """
    ext_arq = get_test_extarq(**kwargs)
    dbapi = db_api.get_instance()
    return dbapi.extarq_create(context, ext_arq)


def get_test_arq(**kwargs):
    return {
        'uuid': kwargs.get('uuid', '10efe63d-dfea-4a37-ad94-4116fba50986'),
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
        'uuid': kw.get('uuid', '10efe63d-dfea-4a37-ad94-4116fba50986'),
        'id': kw.get('id', 1),
        'deployable_id': kw.get('deployable_id', 1),
        'cpid_id': kw.get('cpid_id', 1),
        'in_use': kw.get('in_use', False),
        'attach_type': kw.get('attach_type', "PCI"),
        'attach_info': kw.get('attach_info', "attach_info"),
        'created_at': kw.get('create_at', None),
        'updated_at': kw.get('updated_at', None),
    }


def create_test_attach_handle(context, **kwargs):
    """Create test attach handle entry in DB and return
    AttachHandle DB object.

    Function to be used to create test AttachHandle objects in the database.
    :param context: request context.
    :param kwargs: kwargs which override default attach handle attributes.
    :returns: Test AttachHandle DB object.
    """
    attach_handle = get_test_attach_handle(**kwargs)
    dbapi = db_api.get_instance()
    return dbapi.attach_handle_create(context, attach_handle)


def get_test_control_path(**kw):
    return {
        'uuid': kw.get('uuid', '10efe63d-dfea-4a37-ad94-4116fba50986'),
        'id': kw.get('id', 1),
        'device_id': kw.get('device_id', 1),
        'cpid_type': kw.get('cpid_type', "PCI"),
        'cpid_info': kw.get('cpid_info',
                            '{"device": "2", "bus": "00", "function": "01", '
                            '"domain": "0001"}'),
        'created_at': kw.get('create_at', None),
        'updated_at': kw.get('updated_at', None),
    }


def get_test_device_profile(**kw):
    return {
        'id': kw.get('id', 1),
        'uuid': kw.get('uuid', 'c0f43d55-03bf-4831-8639-9bbdb6be2478'),
        'name': kw.get('name', 'name'),
        'description': kw.get('description', 'fake_dp_desc'),
        'profile_json': kw.get(
            'profile_json',
            '{"version": "1.0", \
             "groups": [{"resources:CUSTOM_ACCELERATOR_FPGA": "1"}, \
             {"trait:CUSTOM_FPGA_INTEL_PAC_ARRIA10": "required"}, \
             {"trait:CUSTOM_FUNCTION_ID_3AFB": "required"}]}'),
        'created_at': kw.get('create_at', None),
        'updated_at': kw.get('updated_at', None),
    }


def create_test_device_profile(context, **kwargs):
    """Create test device profile entry in DB and return
    DeviceProfile DB object.

    Function to be used to create test DeviceProfile objects in the database.
    :param context: request context.
    :param kwargs: kwargs which override default device profile attributes.
    :returns: Test DeviceProfile DB object.
    """
    device_profile = get_test_device_profile(**kwargs)
    dbapi = db_api.get_instance()
    return dbapi.device_profile_create(context, device_profile)
