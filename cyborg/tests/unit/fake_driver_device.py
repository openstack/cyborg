# Copyright 2020 Inspur Technologies Co.,LTD.
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

from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_attribute
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device


def get_fake_driver_devices_as_dict():
    driver_device1 = {
        "vendor": "0xABCD",
        "vendor_board_info": "fake_vendor_info",
        "model": "miss model info",
        "type": "GPU",
        "std_board_info": "{'class': 'Fake class', 'device_id': '0xabcd'}",
        "stub": False,
        "controlpath_id": get_fake_driver_controlpath_objs()[0],
        "deployable_list": get_fake_driver_deployable_objs()[:1]
    }
    driver_device2 = {
        "vendor": "0xDCBA",
        "vendor_board_info": "fake_vendor_info",
        "model": "miss model info",
        "type": "GPU",
        "std_board_info": "{'class': 'Fake class', 'device_id': '0xdcba'}",
        "stub": False,
        "controlpath_id": get_fake_driver_controlpath_objs()[1],
        "deployable_list": get_fake_driver_deployable_objs()[1:]
    }
    return [driver_device1, driver_device2]


def get_fake_driver_devices_objs():
    devices_list = get_fake_driver_devices_as_dict()
    obj_devices = []
    for device in devices_list:
        obj_driver_device = driver_device.DriverDevice()
        for field in device.keys():
            obj_driver_device[field] = device[field]
        obj_devices.append(obj_driver_device)
    return obj_devices


def get_fake_driver_controlpath_as_dict():
    driver_controlpath1 = {
        "cpid_info": '{"bus": "af", "device":00, "domain":0000, "function":0}',
        "cpid_type": "PCI"
    }
    driver_controlpath2 = {
        "cpid_info": '{"bus": "db", "device":00, "domain":0000, "function":0}',
        "cpid_type": "PCI"
    }
    return [driver_controlpath1, driver_controlpath2]


def get_fake_driver_controlpath_objs():
    controlpath_list = get_fake_driver_controlpath_as_dict()
    obj_controlpaths = []
    for controlpath in controlpath_list:
        obj_driver_controlpath = driver_controlpath_id.DriverControlPathID()
        for field in controlpath.keys():
            obj_driver_controlpath[field] = controlpath[field]
        obj_controlpaths.append(obj_driver_controlpath)
    return obj_controlpaths


def get_fake_driver_depolyables_as_dict():
    driver_depolyable1 = {
        "attach_handle_list": get_fake_driver_attach_handle_objs()[:1],
        "attribute_list": get_fake_driver_attribute_objs(),
        "driver_name": "NVIDIA",
        "name": "Tesla V100_0000:af:00.0",
        "num_accelerators": 1,
    }
    driver_depolyable2 = {
        "attach_handle_list": get_fake_driver_attach_handle_objs()[1:],
        "attribute_list": get_fake_driver_attribute_objs(),
        "driver_name": "NVIDIA",
        "name": "Tesla V100_0000:db:00.0",
        "num_accelerators": 1,
    }
    return [driver_depolyable1, driver_depolyable2]


def get_fake_driver_deployable_objs():
    deployables_list = get_fake_driver_depolyables_as_dict()
    obj_deployables = []
    for deployable in deployables_list:
        obj_driver_deployable = driver_deployable.DriverDeployable()
        for field in deployable.keys():
            obj_driver_deployable[field] = deployable[field]
        obj_deployables.append(obj_driver_deployable)
    return obj_deployables


def get_fake_driver_attach_handles_as_dict():
    driver_attach_handle1 = {
        "attach_info":
            '{"bus": "af", "device":00, "domain":0000, "function":0}',
        "attach_type": "PCI",
        "in_use": 0
    }
    driver_attach_handle2 = {
        "attach_info":
            '{"bus": "db", "device":00, "domain":0000, "function":0}',
        "attach_type": "PCI",
        "in_use": 0
    }
    return [driver_attach_handle1, driver_attach_handle2]


def get_fake_driver_attach_handle_objs():
    attach_handles_list = get_fake_driver_attach_handles_as_dict()
    obj_attach_handles = []
    for attach_handle in attach_handles_list:
        obj_driver_attach_handle = driver_attach_handle.DriverAttachHandle()
        for field in attach_handle.keys():
            obj_driver_attach_handle[field] = attach_handle[field]
        obj_attach_handles.append(obj_driver_attach_handle)
    return obj_attach_handles


def get_fake_driver_attributes_as_dict():
    driver_attribute1 = {
        "key": "trait0",
        "value": "CUSTOM_GPU_NVIDIA"
    }
    driver_attribute2 = {
        "key": "trait1",
        "value": "CUSTOM_GPU_PRODUCT_ID_1DB6"
    }
    driver_attribute3 = {
        "key": "rc",
        "value": "PGPU"
    }
    return [driver_attribute1, driver_attribute2, driver_attribute3]


def get_fake_driver_attribute_objs():
    attributes_list = get_fake_driver_attributes_as_dict()
    obj_attributes = []
    for attribute in attributes_list:
        obj_driver_attribute = driver_attribute.DriverAttribute()
        for field in attribute.keys():
            obj_driver_attribute[field] = attribute[field]
        obj_attributes.append(obj_driver_attribute)
    return obj_attributes
