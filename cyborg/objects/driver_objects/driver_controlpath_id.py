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
from cyborg.objects.control_path import ControlpathID
from cyborg.objects import fields as object_fields


@base.CyborgObjectRegistry.register
class DriverControlPathID(base.DriverObjectBase,
                          object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'cpid_type': object_fields.StringField(nullable=False),
        # PCI BDF, PowerVM device, etc.
        'cpid_info': object_fields.StringField(nullable=False)
    }

    def create(self, context, device_id):
        """Create a driver-side ControlPathID for drivers. Call
        ControlpathID object to store in DB.
        """
        cpid_obj = ControlpathID(context=context,
                                 device_id=device_id,
                                 cpid_type=self.cpid_type,
                                 cpid_info=self.cpid_info)
        cpid_obj.create(context)
        return cpid_obj

    def destroy(self, context, device_id):
        cpid_obj = ControlpathID.get_by_device_id_cpidinfo(context,
                                                           device_id,
                                                           self.cpid_info)
        if cpid_obj is not None:
            cpid_obj.destroy(context)

    @classmethod
    def get(cls, context, device_id):
        # return None when can't found any.
        cpid_obj = ControlpathID.get_by_device_id(context, device_id)
        driver_cpid_obj = None
        if cpid_obj is not None:
            driver_cpid_obj = cls(context=context,
                                  cpid_type=cpid_obj.cpid_type,
                                  cpid_info=cpid_obj.cpid_info)
        return driver_cpid_obj
