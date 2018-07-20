# Copyright (c) 2018 Intel.
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
Track resources like FPGA GPU and QAT for a host.  Provides the
conductor with useful information about availability through the accelerator
model.
"""

from oslo_log import log as logging
from oslo_messaging.rpc.client import RemoteError
from oslo_utils import uuidutils

from cyborg.accelerator.drivers.fpga.base import FPGADriver
from cyborg.common import utils
from cyborg import objects


LOG = logging.getLogger(__name__)

AGENT_RESOURCE_SEMAPHORE = "agent_resources"

DEPLOYABLE_VERSION = "1.0"

# need to change the driver field name
DEPLOYABLE_HOST_MAPS = {"assignable": "assignable",
                        "address": "devices",
                        "board": "product_id",
                        "type": "function",
                        "vendor": "vendor_id",
                        "name": "name"}


class ResourceTracker(object):
    """Agent helper class for keeping track of resource usage as instances
    are built and destroyed.
    """

    def __init__(self, host, cond_api):
        # FIXME (Shaohe) local cache for Accelerator.
        # Will fix it in next release.
        self.fpgas = None
        self.host = host
        self.conductor_api = cond_api
        self.fpga_driver = FPGADriver()

    @utils.synchronized(AGENT_RESOURCE_SEMAPHORE)
    def claim(self, context):
        pass

    def _fpga_compare_and_update(self, host_dev, acclerator):
        need_updated = False
        for k, v in DEPLOYABLE_HOST_MAPS.items():
            if acclerator[k] != host_dev[v]:
                need_updated = True
                acclerator[k] = host_dev[v]
        return need_updated

    def _gen_deployable_from_host_dev(self, host_dev):
        dep = {}
        for k, v in DEPLOYABLE_HOST_MAPS.items():
            dep[k] = host_dev[v]
        dep["host"] = self.host
        dep["version"] = DEPLOYABLE_VERSION
        dep["availability"] = "free"
        dep["uuid"] = uuidutils.generate_uuid()
        return dep

    @utils.synchronized(AGENT_RESOURCE_SEMAPHORE)
    def update_usage(self, context):
        """Update the resource usage and stats after a change in an
        instance
        """
        def create_deployable(fpgas, bdf, parent_uuid=None):
            fpga = fpgas[bdf]
            dep = self._gen_deployable_from_host_dev(fpga)
            # if parent_uuid:
            dep["parent_uuid"] = parent_uuid
            obj_dep = objects.Deployable(context, **dep)
            new_dep = self.conductor_api.deployable_create(context, obj_dep)
            return new_dep

        # NOTE(Shaohe Feng) need more agreement on how to keep consistency.
        fpgas = self._get_fpga_devices()
        bdfs = set(fpgas.keys())
        deployables = self.conductor_api.deployable_get_by_host(
            context, self.host)

        # NOTE(Shaohe Feng) when no "address" in deployable?
        accls = dict([(v["address"], v) for v in deployables])
        accl_bdfs = set(accls.keys())

        # Firstly update
        for mutual in accl_bdfs & bdfs:
            accl = accls[mutual]
            if self._fpga_compare_and_update(fpgas[mutual], accl):
                try:
                    self.conductor_api.deployable_update(context, accl)
                except RemoteError as e:
                    LOG.error(e)
        # Add
        new = bdfs - accl_bdfs
        new_pf = set([n for n in new if fpgas[n]["function"] == "pf"])
        for n in new_pf:
            new_dep = create_deployable(fpgas, n)
            accls[n] = new_dep
            sub_vf = set()
            if "regions" in n:
                sub_vf = set([sub["devices"] for sub in fpgas[n]["regions"]])
            for vf in sub_vf & new:
                new_dep = create_deployable(fpgas, vf, new_dep["uuid"])
                accls[vf] = new_dep
                new.remove(vf)
        for n in new - new_pf:
            p_bdf = fpgas[n]["parent_devices"]
            p_accl = accls[p_bdf]
            p_uuid = p_accl["uuid"]
            new_dep = create_deployable(fpgas, n, p_uuid)

        # Delete
        for obsolete in accl_bdfs - bdfs:
            try:
                self.conductor_api.deployable_delete(context, accls[obsolete])
            except RemoteError as e:
                LOG.error(e)
            del accls[obsolete]

    def _get_fpga_devices(self):

        def form_dict(devices, fpgas):
            for v in devices:
                fpgas[v["devices"]] = v
                if "regions" in v:
                    form_dict(v["regions"], fpgas)

        fpgas = {}
        vendors = self.fpga_driver.discover_vendors()
        for v in vendors:
            driver = self.fpga_driver.create(v)
            form_dict(driver.discover(), fpgas)
        return fpgas
