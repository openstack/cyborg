# Copyright 2018 Lenovo (Beijing) Co.,LTD.
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

from oslo_versionedobjects import base as object_base
from cyborg.objects import base
from cyborg.objects import fields as object_fields
from cyborg.objects.driver_objects.driver_deployable import DriverDeployable
from cyborg.objects.driver_objects.driver_controlpath_id import \
    DriverControlPathID


@base.CyborgObjectRegistry.register
class DriverDevice(base.DriverObjectBase,
                   object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        # standard borad info: vendor_id, product_id, remotable?
        'vendor': object_fields.StringField(nullable=False),
        'model': object_fields.StringField(nullable=False),
        'type': object_fields.DeviceTypeField(nullable=False),
        'std_board_info': object_fields.StringField(nullable=True),
        # vendor board info should be a dict: like acc_topology which is used
        # for driver-specific resource provider.
        'vendor_board_info': object_fields.StringField(nullable=True),
        'hostname': object_fields.StringField(nullable=False),
        # Each controlpath_id corresponds to a different PF. For now
        # we are sticking with a single cpid.
        'controlpath_id': object_fields.ObjectField('DriverControlPathID',
                                                    nullable=False),
        'deployable_list': object_fields.ListOfObjectsField('DriverDeployable',
                                                            default=[],
                                                            nullable=False)
    }
