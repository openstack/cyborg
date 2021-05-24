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

from oslo_versionedobjects import fields as object_fields

from cyborg.common import constants

# Import fields from oslo_versionedobjects
EnumField = object_fields.EnumField
IntegerField = object_fields.IntegerField
UUIDField = object_fields.UUIDField
StringField = object_fields.StringField
DateTimeField = object_fields.DateTimeField
BooleanField = object_fields.BooleanField
ObjectField = object_fields.ObjectField
ListOfObjectsField = object_fields.ListOfObjectsField
ListOfStringsField = object_fields.ListOfStringsField
DictOfStringsField = object_fields.DictOfStringsField
IPAddressField = object_fields.IPAddressField
IPNetworkField = object_fields.IPNetworkField
UnspecifiedDefault = object_fields.UnspecifiedDefault
ListOfDictOfNullableStringsField = (
    object_fields.ListOfDictOfNullableStringsField)


class ARQState(object_fields.Enum):
    ALL = constants.ARQ_STATES

    def __init__(self):
        super(ARQState, self).__init__(valid_values=ARQState.ALL)


class ARQStateField(object_fields.BaseEnumField):
    AUTO_TYPE = ARQState()


class DeviceTypeField(object_fields.AutoTypedField):
    AUTO_TYPE = object_fields.Enum(valid_values=constants.DEVICE_TYPE)
