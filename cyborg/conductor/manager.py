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

import oslo_messaging as messaging

from cyborg.conf import CONF
from cyborg import objects
from cyborg.objects.deployable import Deployable
from cyborg.objects.device import Device
from cyborg.objects.attribute import Attribute
from cyborg.objects.attach_handle import AttachHandle
from cyborg.objects.control_path import ControlpathID
from cyborg.objects.driver_objects.driver_attribute import DriverAttribute
from cyborg.objects.driver_objects.driver_controlpath_id import \
    DriverControlPathID
from cyborg.objects.driver_objects.driver_attach_handle import \
    DriverAttachHandle
from cyborg.objects.driver_objects.driver_deployable import DriverDeployable
from cyborg.objects.driver_objects.driver_device import DriverDevice

from oslo_log import log as logging
LOG = logging.getLogger(__name__)


class ConductorManager(object):
    """Cyborg Conductor manager main class."""

    RPC_API_VERSION = '1.0'
    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, topic, host=None):
        super(ConductorManager, self).__init__()
        self.topic = topic
        self.host = host or CONF.host

    def periodic_tasks(self, context, raise_on_error=False):
        pass

    def accelerator_create(self, context, obj_acc):
        """Create a new accelerator.

        :param context: request context.
        :param obj_acc: a changed (but not saved) accelerator object.
        :returns: created accelerator object.
        """
        base_options = {
            'project_id': context.tenant,
            'user_id': context.user
            }
        obj_acc.update(base_options)
        obj_acc.create(context)
        return obj_acc

    def accelerator_update(self, context, obj_acc):
        """Update an accelerator.

        :param context: request context.
        :param obj_acc: an accelerator object to update.
        :returns: updated accelerator object.
        """
        obj_acc.save(context)
        return obj_acc

    def accelerator_delete(self, context, obj_acc):
        """Delete an accelerator.

        :param context: request context.
        :param obj_acc: an accelerator object to delete.
        """
        obj_acc.destroy(context)

    def deployable_create(self, context, obj_dep):
        """Create a new deployable.

        :param context: request context.
        :param obj_dep: a changed (but not saved) obj_dep object.
        :returns: created obj_dep object.
        """
        obj_dep.create(context)
        return obj_dep

    def deployable_update(self, context, obj_dep):
        """Update a deployable.

        :param context: request context.
        :param obj_dep: a deployable object to update.
        :returns: updated deployable object.
        """
        obj_dep.save(context)
        return obj_dep

    def deployable_delete(self, context, obj_dep):
        """Delete a deployable.

        :param context: request context.
        :param obj_dep: a deployable object to delete.
        """
        obj_dep.destroy(context)

    def deployable_get(self, context, uuid):
        """Retrieve a deployable.

        :param context: request context.
        :param uuid: UUID of a deployable.
        :returns: requested deployable object.
        """
        return objects.Deployable.get(context, uuid)

    def deployable_list(self, context):
        """Retrieve a list of deployables.

        :param context: request context.
        :returns: a list of deployable objects.
        """
        return objects.Deployable.list(context)

    def report_data(self, context, hostname, driver_device_list):
        """Update the Cyborg DB in one hostname according to the
        discovered device list.
        :param context: request context.
        :param hostname: agent's hostname.
        :param driver_device_list: a list of driver_device object
        discovered by agent in the host.
        """
        # TODO: Everytime get from the DB?
        # First retrieve the old_device_list from the DB.
        old_driver_device_list = DriverDevice.list(context, hostname)
        # TODO(wangzhh): Remove invalid driver_devices without controlpath_id.
        # Then diff two driver device list.
        self.drv_device_make_diff(context, hostname, old_driver_device_list,
                                  driver_device_list)

    @classmethod
    def drv_device_make_diff(cls, context, host, old_driver_device_list,
                             new_driver_device_list):
        """Compare new driver-side device object list with the old one in
        one host."""
        LOG.info("Start differing devices.")
        # TODO:The placement report will be implemented here.
        # Use cpid.cpid_info to identify whether the device is the same.
        new_cpid_list = [driver_dev_obj.controlpath_id.cpid_info for
                         driver_dev_obj in new_driver_device_list]
        old_cpid_list = [driver_dev_obj.controlpath_id.cpid_info for
                         driver_dev_obj in old_driver_device_list]
        same = set(new_cpid_list) & set(old_cpid_list)
        added = set(new_cpid_list) - same
        deleted = set(old_cpid_list) - same
        for s in same:
            # get the driver_dev_obj, diff the driver_device layer
            new_driver_dev_obj = new_driver_device_list[new_cpid_list.index(s)]
            old_driver_dev_obj = old_driver_device_list[old_cpid_list.index(s)]
            # First, get dev_obj_list from hostname
            device_obj_list = Device.get_list_by_hostname(context, host)
            # Then, use controlpath_id.cpid_info to identiy one Device.
            cpid_info = new_driver_dev_obj.controlpath_id.cpid_info
            for dev_obj in device_obj_list:
                # get cpid_obj, could be empty or only one value.
                cpid_obj = ControlpathID.get_by_device_id_cpidinfo(
                    context, dev_obj.id, cpid_info)
                # find the one cpid_obj with cpid_info
                if cpid_obj is not None:
                    break

            changed_key = ['std_board_info', 'vendor', 'vendor_board_info',
                           'model', 'type']
            for c_k in changed_key:
                if getattr(new_driver_dev_obj, c_k) != getattr(
                        old_driver_dev_obj, c_k):
                    setattr(dev_obj, c_k, getattr(new_driver_dev_obj, c_k))
            dev_obj.save(context)
            # diff the internal layer: driver_deployable
            cls.drv_deployable_make_diff(context, dev_obj.id, cpid_obj.id,
                                         old_driver_dev_obj.deployable_list,
                                         new_driver_dev_obj.deployable_list)
        # device is deleted.
        for d in deleted:
            old_driver_dev_obj = old_driver_device_list[old_cpid_list.index(d)]
            old_driver_dev_obj.destroy(context, host)
        # device is added
        for a in added:
            new_driver_dev_obj = new_driver_device_list[new_cpid_list.index(a)]
            new_driver_dev_obj.create(context, host)

    @classmethod
    def drv_deployable_make_diff(cls, context, device_id, cpid_id,
                                 old_driver_dep_list, new_driver_dep_list):
        """Compare new driver-side deployable object list with the old one in
        one host."""
        # use name to identify whether the deployable is the same.
        LOG.info("Start differing deploybles.")
        new_name_list = [driver_dep_obj.name for driver_dep_obj in
                         new_driver_dep_list]
        old_name_list = [driver_dep_obj.name for driver_dep_obj in
                         old_driver_dep_list]
        same = set(new_name_list) & set(old_name_list)
        added = set(new_name_list) - same
        deleted = set(old_name_list) - same
        for s in same:
            # get the driver_dep_obj, diff the driver_dep layer
            new_driver_dep_obj = new_driver_dep_list[new_name_list.index(s)]
            old_driver_dep_obj = old_driver_dep_list[old_name_list.index(s)]
            # get dep_obj, it won't be None because it stored before.
            dep_obj = Deployable.get_by_name_deviceid(context, s, device_id)
            # update the driver_dep num_accelerators field
            if dep_obj.num_accelerators != new_driver_dep_obj.num_accelerators:
                dep_obj.num_accelerators = new_driver_dep_obj.num_accelerators
                dep_obj.save(context)
            # diff the internal layer: driver_attribute_list
            new_attribute_list = []
            if hasattr(new_driver_dep_obj, 'attribute_list'):
                new_attribute_list = new_driver_dep_obj.attribute_list
            cls.drv_attr_make_diff(context, dep_obj.id,
                                   old_driver_dep_obj.attribute_list,
                                   new_attribute_list)
            # diff the internal layer: driver_attach_hanle_list
            cls.drv_ah_make_diff(context, dep_obj.id, cpid_id,
                                 old_driver_dep_obj.attach_handle_list,
                                 new_driver_dep_obj.attach_handle_list)
        # name is deleted.
        for d in deleted:
            old_driver_dep_obj = old_driver_dep_list[old_name_list.index(d)]
            old_driver_dep_obj.destroy(context, device_id)
        # name is added.
        for a in added:
            new_driver_dep_obj = new_driver_dep_list[new_name_list.index(a)]
            new_driver_dep_obj.create(context, device_id, cpid_id)

    @classmethod
    def drv_attr_make_diff(cls, context, dep_id, old_driver_attr_list,
                           new_driver_attr_list):
        """Diff new dirver-side Attribute Object lists with the old one."""
        LOG.info("Start differing attributes.")
        new_key_list = [driver_attr_obj.key for driver_attr_obj in
                        new_driver_attr_list]
        old_key_list = [driver_attr_obj.key for driver_attr_obj in
                        old_driver_attr_list]
        same = set(new_key_list) & set(old_key_list)
        # key is same, diff the value.
        for s in same:
            # value is not same, update
            new_driver_attr_obj = new_driver_attr_list[new_key_list.index(s)]
            old_driver_attr_obj = old_driver_attr_list[old_key_list.index(s)]
            if new_driver_attr_obj.value != old_driver_attr_obj.value:
                attr_obj = Attribute.get_by_dep_key(context, dep_id, s)
                attr_obj.value = new_driver_attr_obj.value
                attr_obj.save(context)
        # key is deleted.
        deleted = set(old_key_list) - same
        for d in deleted:
            old_driver_attr_obj = old_driver_attr_list[
                old_key_list.index(d)]
            old_driver_attr_obj.destroy(context, dep_id)
        # key is added.
        added = set(new_key_list) - same
        for a in added:
            new_driver_attr_obj = new_driver_attr_list[new_key_list.index(a)]
            new_driver_attr_obj.create(context, dep_id)

    @classmethod
    def drv_ah_make_diff(cls, context, dep_id, cpid_id, old_driver_ah_list,
                         new_driver_ah_list):
        """Diff new dirver-side AttachHandle Object lists with the old one."""
        LOG.info("Start differing attach_handles.")
        new_info_list = [driver_ah_obj.attach_info for driver_ah_obj in
                         new_driver_ah_list]
        old_info_list = [driver_ah_obj.attach_info for driver_ah_obj in
                         old_driver_ah_list]
        same = set(new_info_list) & set(old_info_list)
        LOG.info(new_info_list)
        LOG.info(old_info_list)
        # attach-info is same
        for s in same:
            # get attach_handle obj
            new_driver_ah_obj = new_driver_ah_list[new_info_list.index(s)]
            old_driver_ah_obj = old_driver_ah_list[old_info_list.index(s)]
            changed_key = ['in_use', 'attach_type']
            ah_obj = AttachHandle.get_ah_by_depid_attachinfo(context,
                                                             dep_id, s)
            for c_k in changed_key:
                if getattr(new_driver_ah_obj, c_k) != getattr(
                        old_driver_ah_obj, c_k):
                    setattr(ah_obj, c_k, getattr(new_driver_ah_obj, c_k))
            ah_obj.save(context)
        # attach_info is deleted.
        deleted = set(old_info_list) - same
        for d in deleted:
            old_driver_ah_obj = old_driver_ah_list[old_info_list.index(d)]
            old_driver_ah_obj.destroy(context, dep_id)
        # attach_info is added.
        added = set(new_info_list) - same
        for a in added:
            new_driver_ah_obj = new_driver_ah_list[new_info_list.index(a)]
            new_driver_ah_obj.create(context, dep_id, cpid_id)
