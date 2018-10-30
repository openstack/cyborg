# -*- coding: utf-8 -*-

#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import oslo_messaging as messaging
from oslo_service import periodic_task

from cyborg.accelerator.drivers.fpga.base import FPGADriver
from cyborg.agent.resource_tracker import ResourceTracker
from cyborg.agent.rpcapi import AgentAPI
from cyborg.image.api import API as ImageAPI
from cyborg.conductor import rpcapi as cond_api
from cyborg.conf import CONF


class AgentManager(periodic_task.PeriodicTasks):
    """Cyborg Agent manager main class."""

    RPC_API_VERSION = '1.0'
    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, topic, host=None):
        super(AgentManager, self).__init__(CONF)
        self.topic = topic
        self.host = host or CONF.host
        self.fpga_driver = FPGADriver()
        self.cond_api = cond_api.ConductorAPI()
        self.agent_api = AgentAPI()
        self.image_api = ImageAPI()
        self._rt = ResourceTracker(host, self.cond_api)

    def periodic_tasks(self, context, raise_on_error=False):
        return self.run_periodic_tasks(context, raise_on_error=raise_on_error)

    def hardware_list(self, context, values):
        """List installed hardware."""
        pass

    def fpga_program(self, context, deployable_uuid, image_uuid):
        """ Program a FPGA regoin, image can be a url or local file"""
        # TODO (Shaohe Feng) Get image from glance.
        # And add claim and rollback logical.
        path = self._download_bitstream(context, image_uuid)
        dep = self.cond_api.deployable_get(context, deployable_uuid)
        driver = self.fpga_driver.create(dep.vendor)
        driver.program(dep.address, path)

    def _download_bitstream(self, context, bitstream_uuid):
        """download the bistream

        :param context: the context
        :param bistream_uuid: v4 uuid of the bitstream to reprogram
        :returns: the path to bitstream downloaded, None if fail to download
        """
        download_path = "/tmp/" + bitstream_uuid + ".bin"
        self.image_api.download(context,
                                bitstream_uuid,
                                dest_path=download_path)
        return download_path

    @periodic_task.periodic_task(run_immediately=True)
    def update_available_resource(self, context, startup=True):
        """update all kinds of accelerator resources from their drivers."""
        self._rt.update_usage(context)
