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

import datetime

from oslo_serialization import jsonutils

from cyborg.objects import device_profile

"""
   See note at the start of cyborg/api/controllers/v2/device_profiles.py.
   Device profiles have an API format (which is provided to POST to
   create one) and an object format. The code in this file can provide
   fake device profiles in either format.
"""


def _get_device_profiles_as_dict():
    date1 = datetime.datetime(
        2019, 10, 9, 6, 31, 59,
        tzinfo=datetime.timezone.utc)
    date2 = datetime.datetime(
        2019, 11, 8, 5, 30, 49,
        tzinfo=datetime.timezone.utc)
    dp1 = {
        "id": 1,
        "uuid": u"a95e10ae-b3e3-4eab-a513-1afae6f17c51",
        "name": u'afaas_example_1',
        "description": "fake-afaas_example_1-desc",
        "created_at": date1,
        "updated_at": None,
        "groups": [
            {"resources:ACCELERATOR_FPGA": "1",
             "trait:CUSTOM_FPGA_INTEL_PAC_ARRIA10": "required",
             "trait:CUSTOM_FUNCTION_ID_3AFB": "required",
             },
            {"resources:CUSTOM_ACCELERATOR_FOO": "2",
             "trait:CUSTOM_TRAIT_ALWAYS": "required",
             }
        ]
    }
    dp2 = {
        "id": 2,
        "uuid": u"199c46b7-63a7-431b-aa40-35da4b9420b1",
        "name": u'daas_example_2',
        "created_at": date2,
        "updated_at": None,
        "description": "fake-daas_example_2-desc",
        "groups": [
            {"resources:ACCELERATOR_FPGA": "1",
             "trait:CUSTOM_REGION_ID_3ACD": "required",
             "accel:bitstream_id": "ea0d149c-8555-495b-bc79-608d7bab1260"
             }
        ]
    }
    return [dp1, dp2]


def _convert_to_obj(dp_dict):
    obj_devprof = device_profile.DeviceProfile()
    for field in dp_dict.keys():
        obj_devprof[field] = dp_dict[field]
    return obj_devprof


def _convert_to_db_devprof(dp_dict):
    profile_json_dict = {'groups': dp_dict['groups']}
    profile_json = jsonutils.dumps(profile_json_dict)
    dp_dict['profile_json'] = profile_json
    del dp_dict['groups']
    return dp_dict


def _drop_uuid(dp_dict):
    del dp_dict['uuid']
    return dp_dict


def get_obj_devprofs():
    dp_list = _get_device_profiles_as_dict()
    obj_devprofs = list(map(_convert_to_obj, dp_list))
    return obj_devprofs


def get_api_devprofs(drop_uuid=False):
    dp_list = _get_device_profiles_as_dict()
    if drop_uuid:
        api_devprofs = list(map(_drop_uuid, dp_list))
    else:
        api_devprofs = dp_list
    return api_devprofs


def get_db_devprofs():
    dp_list = _get_device_profiles_as_dict()
    db_devprofs = list(map(_convert_to_db_devprof, dp_list))
    return db_devprofs
