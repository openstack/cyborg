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
from cyborg.objects.driver_objects.driver_attribute import DriverAttribute
from cyborg.objects.driver_objects.driver_attach_handle import \
    DriverAttachHandle


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
        # TODO: add field related to local_memory or just store in the
        # attribute list?
        'attach_handle_list': object_fields.ListOfObjectsField(
            'DriverAttachHandle', default=[], nullable=True)
    }
