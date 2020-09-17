# Copyright 2019 Intel Ltd.
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

"""
Different accelerator handlers for conductor/agent/api/object to call.
"""


from openstack import connection
from oslo_log import log as logging
from oslo_serialization import jsonutils


from cyborg.agent.rpcapi import AgentAPI
from cyborg.common import constants
from cyborg.common import exception
from cyborg.common import placement_client
from cyborg.common import utils
from cyborg.objects import base
from cyborg.objects.ext_arq import ExtARQ


LOG = logging.getLogger(__name__)


@utils.factory_register(ExtARQ, constants.FPGA)
@base.CyborgObjectRegistry.register
class FPGAExtARQ(ExtARQ):
    """FPGA Extra ARQ."""

    def _get_bitstream_id(self):
        bitstream_id = self.device_profile_group.get(
            constants.ACCEL_BITSTREAM_ID)
        return bitstream_id

    def _get_function_id(self):
        function_id = self.device_profile_group.get(
            constants.ACCEL_FUNCTION_ID)
        return function_id

    def _get_bitstream_md_from_bitstream_id(self, bitstream_id):
        """Get bitstream metadata given a bitstream id."""
        conn = connection.Connection(cloud='devstack-admin')
        resp = conn.image.get('/images/' + bitstream_id)
        if resp:
            return resp.json()
        else:
            LOG.warning('Failed to get image for bitstream (%s)',
                        bitstream_id)
            return None

    # TODO(Shaohe) should move to spec handler.
    def _get_bitstream_md_from_function_id(self, function_id):
        """Get bitstream metadata given a function id."""
        # TODO(Shaohe) parametrize this role in config file.
        conn = connection.Connection(cloud='devstack-admin')
        properties = {constants.ACCEL_FUNCTION_ID: function_id}
        resp = conn.image.get('/images', params=properties)
        if resp:
            image_list = resp.json()['images']
            if type(image_list) != list:
                raise exception.InvalidType(
                    obj='image', type=type(image_list),
                    expected='list')
            if len(image_list) != 1:
                raise exception.ExpectedOneObject(obj='image',
                                                  count=len(image_list))
            LOG.info('[arqs:objs] For function id (%s), got '
                     'bitstream id (%s)', function_id,
                     image_list[0]['id'])
            return image_list[0]
        else:
            LOG.warning('Failed to get image for function (%s)',
                        function_id)
            return None

    def _needs_programming(self, context, deployable):
        bs_id = self._get_bitstream_id()
        fun_id = self._get_function_id()
        if all([bs_id, fun_id]):
            self.update_check_state(
                context, constants.ARQ_BIND_FAILED)
            raise exception.InvalidParameterValue(
                'In device profile {0}, only one among bitstream_id '
                'and function_id must be set, but both are set')
        # TODO(Shaohe) Optimize: check if deployable already has
        # bitstream/function
        if any([bs_id, fun_id]):
            LOG.info('[arqs:objs] bind. Programming needed. '
                     'bitstream: (%s) function: (%s) Deployable UUID: (%s)',
                     bs_id or '', fun_id or '', deployable.uuid)
        else:
            # One situation is that fun_id is zero and device_profile
            # has't bitstream. We should return False.
            LOG.info('No programming is required. ')
            return False
        if bs_id and deployable.bitstream_id == bs_id:
            LOG.info('Deployable %s already has the needed '
                     'bitstream %s. Skipping programming.',
                     deployable.uuid, bs_id)
            return False

        return True

    def get_bitstream_md(self, context, deployable, function_id, bitstream_id):
        """Get bitstream metadata from FPGA image."""
        LOG.info("Get bitstream metadata for deployable(uuid:%s).",
                 deployable.uuid)
        # TODO(Shaohe) Check that deployable.device.hostname matches param
        # hostname out of here
        if not self._needs_programming(context, deployable):
            return

        # FPGA aaS or accelerated Function aaS
        bitstream_md = (
            self._get_bitstream_md_from_bitstream_id(bitstream_id)
            if bitstream_id else
            self._get_bitstream_md_from_function_id(function_id))
        if bitstream_md:
            LOG.info('ARQ %s get bitstream metadata:%s from image registry.',
                     self.arq.uuid, bitstream_md)
        else:
            self.update_check_state(
                context, constants.ARQ_BIND_FAILED)
            LOG.error('Can not get bitstream metadata from image registry '
                      'for ARQ %s', self.arq.uuid)
        return bitstream_md

    def _need_extra_bind_job(self, context, deployable):
        return self._needs_programming(context, deployable)

    @utils.wrap_job_tb("Error during ARQ bind job. Reason: %s")
    def bind(self, context, deployable):
        LOG.info('Start bind jobs for ARQ(%s) with deployable(%s)',
                 self.arq.uuid, deployable.uuid)
        bs_id = self._get_bitstream_id()
        fun_id = self._get_function_id()
        bs_md = self.get_bitstream_md(context, deployable, fun_id, bs_id)
        ok = False
        if bs_md:
            ok = self._do_programming(context, deployable, bs_md['id'])
        if ok:
            fun_id = fun_id or bs_md[constants.ACCEL_FUNCTION_ID]
            self._update_placement(context, fun_id, deployable.driver_name)
            deployable.update(context, {'bitstream_id': bs_md['id']})

        super(FPGAExtARQ, self).bind(context, deployable)

        return True

    def _unbind(self):
        # TODO(Shaohe) add cancel _update_placement, unbind operation.
        pass

    def _delete(self):
        # TODO(Shaohe) add cancel _update_placement, delete operation.
        pass

    def _update_placement(self, context, function_id, driver_name):
        """update resources provider after program."""
        # TODO(Sundar) Don't apply function trait if bitstream is private
        if not function_id:
            LOG.info("Not get function id for resources provider %s.",
                     self.arq.device_rp_uuid)
            return

        placement = placement_client.PlacementClient()
        try:
            placement.delete_traits_with_prefixes(
                self.arq.device_rp_uuid, [constants.FPGA_FUNCTION_ID])
        except Exception as e:
            LOG.error("Failed to delete traits(%s) from resources provider %s."
                      "Reason: %s", constants.FPGA_FUNCTION_ID,
                      self.arq.device_rp_uuid, e.message)
            self.update_check_state(
                context, constants.ARQ_BIND_FAILED)
            raise

        function_id = function_id.upper().replace('-', '_-')
        # TODO(Sundar) Validate this is a valid trait name
        vendor = driver_name.upper()
        trait_names = ["_".join((
            constants.FPGA_FUNCTION_ID, vendor, function_id))]
        try:
            placement.add_traits_to_rp(
                self.arq.device_rp_uuid, trait_names)
        except Exception as e:
            LOG.error("Failed to add traits(%s) to resources provider %s."
                      "Reason: %s", trait_names,
                      self.arq.device_rp_uuid, e.message)
            # TODO(Shaohe) Rollback? We have _update_placement,
            # should cancel it.
            self.update_check_state(
                context, constants.ARQ_BIND_FAILED)
            raise
        LOG.info("Add traits(%s) to resources provider %s.",
                 trait_names, self.arq.device_rp_uuid)

    def _do_programming(self, context, deployable, bitstream_id):
        """FPGA program."""
        hostname = self.arq.hostname
        driver_name = deployable.driver_name

        # query_filter = {"device_id": deployable.device_id}
        # TODO(Shaohe) We should probably get cpid from objects layer,
        # not db layer
        cpid_list = deployable.get_cpid_list(context)
        count = len(cpid_list)
        if count != 1:
            self.update_check_state(
                context, constants.ARQ_BIND_FAILED)
            raise exception.ExpectedOneObject(type='controlpath_id',
                                              count=count)
        controlpath_id = cpid_list[0]
        controlpath_id['cpid_info'] = jsonutils.loads(
            controlpath_id['cpid_info'])
        LOG.info('Found control path id: %s', controlpath_id)

        LOG.info('Starting programming for host: (%s) deployable (%s) '
                 'bitstream_id (%s)', hostname,
                 deployable.uuid, bitstream_id)
        # TODO(Shaohe) do this asynchronously, do this in conductor or agent?
        try:
            agent = AgentAPI()
            agent.fpga_program(context, hostname,
                               controlpath_id, bitstream_id,
                               driver_name)
        except Exception as e:
            self.update_check_state(
                context, constants.ARQ_BIND_FAILED)
            LOG.error('Failed programming for host: (%s) deployable (%s). '
                      'Error: %s', hostname, deployable.uuid, e.message)
            raise
        LOG.info('Finished programming for host: (%s) deployable (%s)',
                 hostname, deployable.uuid)
        # TODO(Shaohe) propagate agent errors to caller
        return True
