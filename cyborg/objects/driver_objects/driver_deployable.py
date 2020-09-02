# Copyright 2018 Lenovo (Beijing) Inc.
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
from cyborg.objects.deployable import Deployable
from cyborg.objects.driver_objects.driver_attach_handle import \
    DriverAttachHandle
from cyborg.objects.driver_objects.driver_attribute import DriverAttribute
from cyborg.objects import fields as object_fields


@base.CyborgObjectRegistry.register
class DriverDeployable(base.DriverObjectBase,
                       object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'name': object_fields.StringField(nullable=False),
        'num_accelerators': object_fields.IntegerField(nullable=False),
        'attribute_list': object_fields.ListOfObjectsField(
            'DriverAttribute', default=[], nullable=True),
        # TODO() add field related to local_memory or just store in the
        # attribute list?
        'attach_handle_list': object_fields.ListOfObjectsField(
            'DriverAttachHandle', default=[], nullable=True),
        'driver_name': object_fields.StringField(nullable=True)
    }

    def create(self, context, device_id, cpid_id):
        """Create a driver-side Deployable object into DB. This object will be
        stored in separate db tables: deployable & attach_handle &
        attribute table.
        """

        # first store in deployable table through Deployable Object.
        deployable_obj = Deployable(context=context,
                                    name=self.name,
                                    num_accelerators=self.num_accelerators,
                                    device_id=device_id,
                                    driver_name=self.driver_name
                                    )
        deployable_obj.create(context)
        # create attribute_list for this deployable
        if hasattr(self, 'attribute_list'):
            for driver_attr in self.attribute_list:
                driver_attr.create(context, deployable_obj.id)

        # create attach_handle_list for this deployable
        if hasattr(self, 'attach_handle_list'):
            for driver_attach_handle in self.attach_handle_list:
                driver_attach_handle.create(context, deployable_obj.id,
                                            cpid_id)

    def destroy(self, context, device_id):
        """delete one driver-side deployable by calling existing Deployable
        and AttachHandle Object. Use name&host to identify Deployable and
        attach_info to identify the AttachHandle
        """

        # get deployable_id by name, get only one value.
        dep_obj = Deployable.get_by_name_deviceid(context, self.name,
                                                  device_id)
        # delete attach_handle
        if hasattr(self, 'attach_handle_list'):
            for driver_ah_obj in self.attach_handle_list:
                # get attach_handle_obj, exist and only one.
                driver_ah_obj.destroy(context, dep_obj.id)
        # delete attribute_list
        if hasattr(self, 'attribute_list'):
            DriverAttribute.destroy(context, dep_obj.id)
        # delete dep_obj
        if dep_obj is not None:
            dep_obj.destroy(context)

    @classmethod
    def list(cls, context, device_id):
        """Form driver-side Deployable object list from DB for one device."""
        # get deployable_obj_list for one device_id
        dep_obj_list = Deployable.get_list_by_device_id(context, device_id)
        driver_dep_obj_list = []
        for dep_obj in dep_obj_list:
            # get driver_ah_obj_list for this dep_obj
            driver_ah_obj_list = DriverAttachHandle.list(context, dep_obj.id)
            # get driver_attr_obj_list fro this dep_obj
            driver_attr_obj_list = DriverAttribute.list(context, dep_obj.id)
            driver_dep_obj = cls(context=context,
                                 name=dep_obj.name,
                                 num_accelerators=dep_obj.num_accelerators,
                                 attribute_list=driver_attr_obj_list,
                                 attach_handle_list=driver_ah_obj_list)
            driver_dep_obj_list.append(driver_dep_obj)
        return driver_dep_obj_list

    @classmethod
    def get_by_name(cls, context, name):
        """Form driver-side Deployable object list from DB for one device."""
        # get deployable_obj_list for one device_id
        dep_obj = Deployable.get_by_name(context, name)
        driver_ah_obj_list = DriverAttachHandle.list(context, dep_obj.id)
        # get driver_attr_obj_list fro this dep_obj
        driver_attr_obj_list = DriverAttribute.list(context, dep_obj.id)
        driver_dep_obj = cls(context=context, name=dep_obj.name,
                             num_accelerators=dep_obj.num_accelerators,
                             attribute_list=driver_attr_obj_list,
                             attach_handle_list=driver_ah_obj_list)
        return driver_dep_obj
