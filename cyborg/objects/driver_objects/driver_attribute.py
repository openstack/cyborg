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

from cyborg.objects.attribute import Attribute
from cyborg.objects import base
from cyborg.objects import fields as object_fields


@base.CyborgObjectRegistry.register
class DriverAttribute(base.DriverObjectBase,
                      object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'key': object_fields.StringField(nullable=False),
        'value': object_fields.StringField(nullable=False)
    }

    def create(self, context, deployable_id):
        """Convert driver-side Attribute into Attribute Object so as to
        store in DB.
        """
        attr_obj = Attribute()
        attr_obj.deployable_id = deployable_id
        attr_obj.set_key_value_pair(self.key, self.value)
        attr_obj.create(context)

    @classmethod
    def destroy(cls, context, deployable_id):
        """Delete driver-side attribute list from the DB."""
        attr_obj_list = Attribute.get_by_deployable_id(context, deployable_id)
        for attr_obj in attr_obj_list:
            attr_obj.destroy(context)

    @classmethod
    def delete_by_key(cls, context, deployable_id, key):
        """Delete driver-side attribute list from the DB."""
        attr_obj_list = Attribute.get_by_deployable_id(context, deployable_id)
        for attr_obj in attr_obj_list:
            if key == attr_obj.key:
                attr_obj.destroy(context)

    @classmethod
    def list(cls, context, deployable_id):
        """Form driver-side attribute list for one deployable."""
        attr_obj_list = Attribute.get_by_deployable_id(context, deployable_id)
        driver_attr_obj_list = []
        for attr_obj in attr_obj_list:
            driver_attr_obj = cls(context=context,
                                  key=attr_obj.key,
                                  value=attr_obj.value)
            driver_attr_obj_list.append(driver_attr_obj)
        return driver_attr_obj_list
