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

from oslo_log import log as logging
import oslo_messaging as messaging
import uuid

from cyborg.common import exception
from cyborg.common import placement_client
from cyborg.conf import CONF
from cyborg.objects.attach_handle import AttachHandle
from cyborg.objects.attribute import Attribute
from cyborg.objects.control_path import ControlpathID
from cyborg.objects.deployable import Deployable
from cyborg.objects.device import Device
from cyborg.objects.driver_objects.driver_device import DriverDeployable
from cyborg.objects.driver_objects.driver_device import DriverDevice
from cyborg.objects.ext_arq import ExtARQ

LOG = logging.getLogger(__name__)


class ConductorManager(object):
    """Cyborg Conductor manager main class."""

    RPC_API_VERSION = '1.0'
    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, topic, host=None):
        super(ConductorManager, self).__init__()
        self.topic = topic
        self.host = host or CONF.host
        self.placement_client = placement_client.PlacementClient()

    def periodic_tasks(self, context, raise_on_error=False):
        pass

    def device_profile_create(self, context, obj_devprof):
        """Signal to conductor service to create a device_profile.

        :param context: request context.
        :param obj_devprof: a created (but not saved) device_profile object.
        :returns: created device_profile object.
        """
        obj_devprof.create(context)
        return obj_devprof

    def device_profile_delete(self, context, obj_devprof):
        """Signal to conductor service to delete a device_profile.
        :param context: request context.
        :param obj_devprof: a device_profile object to delete.
        """
        obj_devprof.destroy(context)

    def arq_create(self, context, obj_extarq, devprof_id):
        """Signal to conductor service to create an accelerator requests.

        :param context: request context.
        :param obj_extarq: a created (but not saved) accelerator_requests
        object
        :param devprof_id: a device profile id
        :returns: saved accelerator_requests object.
        """
        obj_extarq.create(context, devprof_id)
        return obj_extarq

    def arq_delete_by_uuid(self, context, arqs):
        """Signal to conductor service to delete accelerator requests by
        ARQ UUIDs.

        :param context: request context.
        :param arqs: ARQ UUIDs joined with ','
        """
        arqlist = arqs.split(',')
        ExtARQ.delete_by_uuid(context, arqlist)

    def arq_delete_by_instance_uuid(self, context, instance):
        """Signal to conductor service to delete accelerator requests by
        instance UUID.

        :param context: request context.
        :param instance: UUID of instance whose ARQs need to be deleted
        """
        ExtARQ.delete_by_instance(context, instance)

    def arq_apply_patch(self, context, patch_list, valid_fields):
        """Signal to conductor service to apply patch accelerator requests.

        :param context: request context.
        :param patch_list: A map from ARQ UUIDs to their JSON patches
        :param valid_fields: Dict of valid fields
        """
        ExtARQ.apply_patch(context, patch_list, valid_fields)

    def report_data(self, context, hostname, driver_device_list):
        """Update the Cyborg DB in one hostname according to the
        discovered device list.
        :param context: request context.
        :param hostname: agent's hostname.
        :param driver_device_list: a list of driver_device object
        discovered by agent in the host.
        """
        # TODO(): Everytime get from the DB?
        # First retrieve the old_device_list from the DB.
        old_driver_device_list = DriverDevice.list(context, hostname)
        # TODO(wangzhh): Remove invalid driver_devices without controlpath_id.
        # Then diff two driver device list.
        self.drv_device_make_diff(context, hostname,
                                  old_driver_device_list, driver_device_list)

    def drv_device_make_diff(self, context, host, old_driver_device_list,
                             new_driver_device_list):
        """Compare new driver-side device object list with the old one in
        one host.
        """
        LOG.info("Start differing devices.")
        # TODO(): The placement report will be implemented here.
        # Use cpid.cpid_info to identify whether the device is the same.
        stub_cpid_list = [driver_dev_obj.controlpath_id.cpid_info for
                          driver_dev_obj in new_driver_device_list
                          if driver_dev_obj.stub]
        new_cpid_list = [driver_dev_obj.controlpath_id.cpid_info for
                         driver_dev_obj in new_driver_device_list]
        old_cpid_list = [driver_dev_obj.controlpath_id.cpid_info for
                         driver_dev_obj in old_driver_device_list]
        same = set(new_cpid_list) & set(old_cpid_list) - set(stub_cpid_list)
        added = set(new_cpid_list) - same - set(stub_cpid_list)
        deleted = set(old_cpid_list) - same - set(stub_cpid_list)
        host_rp = self._get_root_provider(context, host)
        # device is deleted.
        for d in deleted:
            old_driver_dev_obj = old_driver_device_list[old_cpid_list.index(d)]
            for driver_dep_obj in old_driver_dev_obj.deployable_list:
                rp_uuid = self.get_rp_uuid_from_obj(driver_dep_obj)
                self._delete_provider_and_sub_providers(context, rp_uuid)
            old_driver_dev_obj.destroy(context, host)
        # device is added
        for a in added:
            new_driver_dev_obj = new_driver_device_list[new_cpid_list.index(a)]
            try:
                new_driver_dev_obj.create(context, host)
            except Exception as exc:
                LOG.exception("Failed to add device %(device)s. "
                              "Reason: %(reason)s",
                              {'device': new_driver_dev_obj,
                               'reason': exc})
                new_driver_dev_obj.destroy(context, host)
            # TODO(All): If report device data to Placement raise exception,
            # we should revert driver device created in Cyborg and resources
            # created in Placement to reduce the risk of data inconsistency
            # here between Cyborg and Placement.
            cleanup_inconsistency_resources = False
            for driver_dep_obj in new_driver_dev_obj.deployable_list:
                try:
                    self.get_placement_needed_info_and_report(context,
                                                              driver_dep_obj,
                                                              host_rp)
                except Exception as exc:
                    LOG.info("Failed to add device %(device)s. "
                             "Reason: %(reason)s",
                             {'device': new_driver_dev_obj,
                              'reason': exc})
                    cleanup_inconsistency_resources = True
                    break
            if cleanup_inconsistency_resources:
                new_driver_dev_obj.destroy(context, host)
                for driver_dep_obj in new_driver_dev_obj.deployable_list:
                    rp_uuid = self.get_rp_uuid_from_obj(driver_dep_obj)
                    self._delete_provider_and_sub_providers(context, rp_uuid)
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
            self.drv_deployable_make_diff(context, dev_obj.id, cpid_obj.id,
                                          old_driver_dev_obj.deployable_list,
                                          new_driver_dev_obj.deployable_list,
                                          host_rp)

    def drv_deployable_make_diff(self, context, device_id, cpid_id,
                                 old_driver_dep_list, new_driver_dep_list,
                                 host_rp):
        """Compare new driver-side deployable object list with the old one in
        one host.
        """
        # use name to identify whether the deployable is the same.
        LOG.info("Start differing deploybles.")
        new_name_list = [driver_dep_obj.name for driver_dep_obj in
                         new_driver_dep_list]
        old_name_list = [driver_dep_obj.name for driver_dep_obj in
                         old_driver_dep_list]
        same = set(new_name_list) & set(old_name_list)
        added = set(new_name_list) - same
        deleted = set(old_name_list) - same
        # name is deleted.
        for d in deleted:
            old_driver_dep_obj = old_driver_dep_list[old_name_list.index(d)]
            rp_uuid = self.get_rp_uuid_from_obj(old_driver_dep_obj)
            old_driver_dep_obj.destroy(context, device_id)
            self._delete_provider_and_sub_providers(context, rp_uuid)
        # name is added.
        for a in added:
            new_driver_dep_obj = new_driver_dep_list[new_name_list.index(a)]
            new_driver_dep_obj.create(context, device_id, cpid_id)
            try:
                self.get_placement_needed_info_and_report(context,
                                                          new_driver_dep_obj,
                                                          host_rp)
            except Exception as exc:
                LOG.info("Failed to add deployable %(deployable)s. "
                         "Reason: %(reason)s",
                         {'deployable': new_driver_dep_obj,
                          'reason': exc})
                new_driver_dep_obj.destroy(context, device_id)
                rp_uuid = self.get_rp_uuid_from_obj(new_driver_dep_obj)
                # TODO(All): If report deployable data to Placement raise
                # exception, we should revert driver deployable created in
                # Cyborg and resources created in Placement to reduce the risk
                # of data inconsistency here between Cyborg and Placement.
                self._delete_provider_and_sub_providers(context, rp_uuid)
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
                rp_uuid = self.get_rp_uuid_from_obj(new_driver_dep_obj)
                attrs = new_driver_dep_obj.attribute_list
                resource_class = [i.value for i in attrs if i.key == 'rc'][0]
                inv_data = _gen_resource_inventory(
                    resource_class, dep_obj.num_accelerators)
                self.placement_client.update_inventory(rp_uuid, inv_data)
            # diff the internal layer: driver_attribute_list
            new_attribute_list = []
            if hasattr(new_driver_dep_obj, 'attribute_list'):
                new_attribute_list = new_driver_dep_obj.attribute_list
            self.drv_attr_make_diff(context, dep_obj.id,
                                    old_driver_dep_obj.attribute_list,
                                    new_attribute_list)
            # diff the internal layer: driver_attach_hanle_list
            self.drv_ah_make_diff(context, dep_obj.id, cpid_id,
                                  old_driver_dep_obj.attach_handle_list,
                                  new_driver_dep_obj.attach_handle_list)

    def drv_attr_make_diff(self, context, dep_id, old_driver_attr_list,
                           new_driver_attr_list):
        """Diff new driver-side Attribute Object lists with the old one."""
        LOG.info("Start differing attributes.")
        dep_obj = Deployable.get_by_id(context, dep_id)
        driver_dep = DriverDeployable.get_by_name(context, dep_obj.name)
        rp_uuid = self.get_rp_uuid_from_obj(driver_dep)
        new_key_list = [driver_attr_obj.key for driver_attr_obj in
                        new_driver_attr_list]
        old_key_list = [driver_attr_obj.key for driver_attr_obj in
                        old_driver_attr_list]
        same = set(new_key_list) & set(old_key_list)
        # key is deleted.
        deleted = set(old_key_list) - same
        for d in deleted:
            old_driver_attr_obj = old_driver_attr_list[old_key_list.index(d)]
            self.placement_client.delete_trait_by_name(
                context, rp_uuid, old_driver_attr_obj.value)
            old_driver_attr_obj.delete_by_key(context, dep_id, d)
        # key is added.
        added = set(new_key_list) - same
        for a in added:
            new_driver_attr_obj = new_driver_attr_list[new_key_list.index(a)]
            new_driver_attr_obj.create(context, dep_id)
            self.placement_client.add_traits_to_rp(
                rp_uuid, [new_driver_attr_obj.value])
        # key is same, diff the value.
        for s in same:
            # value is not same, update
            new_driver_attr_obj = new_driver_attr_list[new_key_list.index(s)]
            old_driver_attr_obj = old_driver_attr_list[old_key_list.index(s)]
            if new_driver_attr_obj.value != old_driver_attr_obj.value:
                attr_obj = Attribute.get_by_dep_key(context, dep_id, s)
                attr_obj.value = new_driver_attr_obj.value
                attr_obj.save(context)
                # Update traits here.
                if new_driver_attr_obj.key.startswith("trait"):
                    self.placement_client.delete_trait_by_name(
                        context, rp_uuid, old_driver_attr_obj.value)
                    self.placement_client.add_traits_to_rp(
                        rp_uuid, [new_driver_attr_obj.value])
                # Update resource classes here.
                if new_driver_attr_obj.key.startswith("rc"):
                    self.placement_client.ensure_resource_classes(
                        context, [new_driver_attr_obj.value])
                    inv_data = _gen_resource_inventory(
                        new_driver_attr_obj.value, dep_obj.num_accelerators)
                    self.placement_client.update_inventory(rp_uuid, inv_data)
                    self.placement_client.delete_rc_by_name(
                        context, old_driver_attr_obj.value)

    @classmethod
    def drv_ah_make_diff(cls, context, dep_id, cpid_id, old_driver_ah_list,
                         new_driver_ah_list):
        """Diff new driver-side AttachHandle Object lists with the old one."""
        LOG.info("Start differing attach_handles.")
        new_info_list = [driver_ah_obj.attach_info for driver_ah_obj in
                         new_driver_ah_list]
        old_info_list = [driver_ah_obj.attach_info for driver_ah_obj in
                         old_driver_ah_list]
        same = set(new_info_list) & set(old_info_list)
        LOG.info('new info list %s', new_info_list)
        LOG.info('old info list %s', old_info_list)
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
        # attach-info is same
        for s in same:
            # get attach_handle obj
            new_driver_ah_obj = new_driver_ah_list[new_info_list.index(s)]
            old_driver_ah_obj = old_driver_ah_list[old_info_list.index(s)]
            changed_key = ['attach_type']
            ah_obj = AttachHandle.get_ah_by_depid_attachinfo(context,
                                                             dep_id, s)
            for c_k in changed_key:
                if getattr(new_driver_ah_obj, c_k) != getattr(
                        old_driver_ah_obj, c_k):
                    setattr(ah_obj, c_k, getattr(new_driver_ah_obj, c_k))
            ah_obj.save(context)

    def _get_root_provider(self, context, hostname):
        try:
            provider = self.placement_client.get(
                "resource_providers?name=" + hostname).json()
            pr_uuid = provider["resource_providers"][0]["uuid"]
            return pr_uuid
        except IndexError:
            raise exception.PlacementResourceProviderNotFound(
                resource_provider=hostname)

    def _get_sub_provider(self, context, parent, name):
        old_sub_pr_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS,
                                         str(name)))
        new_sub_pr_uuid = self.placement_client.ensure_resource_provider(
            context, old_sub_pr_uuid,
            name=name, parent_provider_uuid=parent)
        if old_sub_pr_uuid == new_sub_pr_uuid:
            return new_sub_pr_uuid
        else:
            raise exception.Conflict()

    def provider_report(self, context, name, resource_class, traits, total,
                        parent):
        self.placement_client.ensure_resource_classes(
            context, [resource_class])
        sub_pr_uuid = self._get_sub_provider(
            context, parent, name)
        result = _gen_resource_inventory(resource_class, total)
        self.placement_client.update_inventory(sub_pr_uuid, result)
        # traits = ["CUSTOM_FPGA_INTEL", "CUSTOM_FPGA_INTEL_ARRIA10",
        #           "CUSTOM_FPGA_INTEL_REGION_UUID",
        #           "CUSTOM_FPGA_FUNCTION_ID_INTEL_UUID",
        #           "CUSTOM_PROGRAMMABLE",
        #           "CUSTOM_FPGA_NETWORK"]
        self.placement_client.add_traits_to_rp(sub_pr_uuid, traits)
        return sub_pr_uuid

    def get_placement_needed_info_and_report(self, context, obj,
                                             parent_uuid=None):
        pr_name = obj.name
        attrs = obj.attribute_list
        resource_class = [i.value for i in attrs if i.key == 'rc'][0]
        traits = [i.value for i in attrs
                  if str(i.key).startswith("trait")]
        total = obj.num_accelerators
        rp_uuid = self.provider_report(context, pr_name, resource_class,
                                       traits, total, parent_uuid)
        dep_obj = Deployable.get_by_name(context, pr_name)
        dep_obj["rp_uuid"] = rp_uuid
        dep_obj.save(context)

    def get_rp_uuid_from_obj(self, obj):
        return str(uuid.uuid3(uuid.NAMESPACE_DNS, str(obj.name)))

    def _delete_provider_and_sub_providers(self, context, rp_uuid):
        rp_in_tree = self.placement_client.get_providers_in_tree(context,
                                                                 rp_uuid)
        for rp in rp_in_tree[::-1]:
            if rp["parent_provider_uuid"] == rp_uuid or rp["uuid"] == rp_uuid:
                self.placement_client.delete_provider(rp["uuid"])
                LOG.info("Sucessfully delete resource provider %(rp_uuid)s",
                         {"rp_uuid": rp["uuid"]})
                if rp["uuid"] == rp_uuid:
                    break


def _gen_resource_inventory(resource_class, total):
    return {
        resource_class: {
            'total': total,
            'max_unit': total,
        },
    }
