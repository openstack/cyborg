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

from oslo_log import log as logging
from oslo_versionedobjects import base as object_base

from cyborg.objects.attach_handle import AttachHandle
from cyborg.objects import base
from cyborg.objects import fields as object_fields
LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class DriverAttachHandle(base.DriverObjectBase,
                         object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'attach_type': object_fields.StringField(nullable=False),
        # PCI BDF or mediated device ID...
        'attach_info': object_fields.StringField(nullable=False),
        # The status of attach_handle, is in use or not.
        'in_use': object_fields.BooleanField(nullable=False, default=False)
    }

    def create(self, context, deployable_id, cpid_id):
        """Create a driver-side AttachHandle object, call AttachHandle
        Object to store in DB.
        """
        attach_handle_obj = AttachHandle(context=context,
                                         deployable_id=deployable_id,
                                         cpid_id=cpid_id,
                                         attach_type=self.attach_type,
                                         attach_info=self.attach_info,
                                         in_use=self.in_use
                                         )
        attach_handle_obj.create(context)

    def destroy(self, context, deployable_id):
        ah_obj = AttachHandle.get_ah_by_depid_attachinfo(context,
                                                         deployable_id,
                                                         self.attach_info)
        if ah_obj is not None:
            ah_obj.destroy(context)

    @classmethod
    def list(cls, context, deployable_id):
        """Form a driver-side attach_handle list for one deployable."""
        ah_obj_list = AttachHandle.get_ah_list_by_deployable_id(
            context, deployable_id)
        driver_ah_obj_list = []
        for ah_obj in ah_obj_list:
            driver_ah_obj = cls(context=context,
                                attach_type=ah_obj.attach_type,
                                attach_info=ah_obj.attach_info,
                                in_use=ah_obj.in_use)
            driver_ah_obj_list.append(driver_ah_obj)
        return driver_ah_obj_list
