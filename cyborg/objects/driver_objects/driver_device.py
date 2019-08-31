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
from cyborg.objects.device import Device
from cyborg.objects.driver_objects.driver_controlpath_id import \
    DriverControlPathID
from cyborg.objects.driver_objects.driver_deployable import DriverDeployable
from cyborg.objects import fields as object_fields


@base.CyborgObjectRegistry.register
class DriverDevice(base.DriverObjectBase,
                   object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'vendor': object_fields.StringField(nullable=False),
        'model': object_fields.StringField(nullable=False),
        'type': object_fields.DeviceTypeField(nullable=False),
        'std_board_info': object_fields.StringField(nullable=True),
        # vendor board info should be a dict for driver-specific resource
        # provider.
        'vendor_board_info': object_fields.StringField(nullable=True),
        # hostname will be set by the agent, so driver don't need to report.
        # Each controlpath_id corresponds to a different PF. For now
        # we are sticking with a single cpid.
        'controlpath_id': object_fields.ObjectField('DriverControlPathID',
                                                    nullable=False),
        'deployable_list': object_fields.ListOfObjectsField('DriverDeployable',
                                                            default=[],
                                                            nullable=False),
        'stub': object_fields.BooleanField(nullable=False, default=False)
    }

    def create(self, context, host):
        """Create a driver-side Device Object into DB. This object will be
        stored in many db tables: device, deployable, attach_handle,
        controlpath_id etc. by calling related Object.
        """
        # first store in device table through Device Object.

        device_obj = Device(context=context,
                            type=self.type,
                            vendor=self.vendor,
                            model=self.model,
                            hostname=host
                            )
        if hasattr(self, 'std_board_info'):
            device_obj.std_board_info = self.std_board_info
        if hasattr(self, 'vendor_board_info'):
            device_obj.vendor_board_info = self.vendor_board_info
        device_obj.create(context)

        # for the controlpath_id, call driver_controlpath_id to create.
        cpid_obj = self.controlpath_id.create(context, device_obj.id)
        # for deployable_list, call internal layer object: driver_deployable
        # to create.
        for driver_deployable in self.deployable_list:
            driver_deployable.create(context, device_obj.id, cpid_obj.id)

    def destroy(self, context, host):
        """Delete a driver-side Device Object from db. This should
        delete the internal layer objects.
        """
        # get dev_obj_list from hostname
        device_obj = self.get_device_obj(context, host)
        # delete deployable_list first.
        for driver_deployable in self.deployable_list:
            driver_deployable.destroy(context, device_obj.id)
        if hasattr(self.controlpath_id, 'cpid_info'):
            cpid_obj = ControlpathID.get_by_device_id_cpidinfo(
                context, device_obj.id, self.controlpath_id.cpid_info)
            # delete controlpath_id
            cpid_obj.destroy(context)
        # delete the device
        device_obj.destroy(context)

    def get_device_obj(self, context, host):
        """Get a driver-side Device Object from db.

        :param context: requested context.
        :param host: hostname of the node.
        :return: a device object of current driver device object. It will
        return on value because it has controlpath_id.
        """
        # get dev_obj_list from hostname
        device_obj_list = Device.get_list_by_hostname(context, host)
        # use controlpath_id.cpid_info to identiy one Device.
        for device_obj in device_obj_list:
            # get cpid_obj, could be empty or only one value.
            cpid_obj = ControlpathID.get_by_device_id_cpidinfo(
                context, device_obj.id, self.controlpath_id.cpid_info)
            # find the one cpid_obj with cpid_info
            if cpid_obj is not None:
                return device_obj

    @classmethod
    def list(cls, context, host):
        """Form driver-side device object list from DB for one host.
        A list may contains driver_device_object without controlpath_id.(In
        the case some of controlpath_id can't store successfully but its
        devices stores successfully.)
        """
        # get dev_obj_list from hostname
        dev_obj_list = Device.get_list_by_hostname(context, host)
        driver_dev_obj_list = []
        for dev_obj in dev_obj_list:
            cpid = DriverControlPathID.get(context, dev_obj.id)
            # NOTE: will not return device without controlpath_id.
            if cpid is not None:
                driver_dev_obj = \
                    cls(context=context, vendor=dev_obj.vendor,
                        model=dev_obj.model, type=dev_obj.type,
                        std_board_info=dev_obj.std_board_info,
                        vendor_board_info=dev_obj.vendor_board_info,
                        controlpath_id=cpid,
                        deployable_list=DriverDeployable.list(context,
                                                              dev_obj.id)
                        )
                driver_dev_obj_list.append(driver_dev_obj)
        return driver_dev_obj_list

    def get_device_obj_by_device_id(self, context, device_id):
        """Get device object by device id.

        :param context: requested context.
        :param host: hostname of the node.
        :return: a device object of current driver device object. It will
        return on value because it has controlpath_id.
        """
        # get dev_obj_list from hostname
        device_obj = Device.get_by_device_id(context, device_id)
        # use controlpath_id.cpid_info to identiy one Device.
        # get cpid_obj, could be empty or only one value.
        ControlpathID.get_by_device_id_cpidinfo(
            context, device_obj.id, self.controlpath_id.cpid_info)
        # find the one cpid_obj with cpid_info
        return device_obj
