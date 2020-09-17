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

import os
import tempfile

from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import periodic_task
from oslo_utils import uuidutils

from cyborg.accelerator.drivers.fpga.base import FPGADriver
from cyborg.agent.resource_tracker import ResourceTracker
from cyborg.agent.rpcapi import AgentAPI
from cyborg.common import exception
from cyborg.conductor import rpcapi as cond_api
from cyborg.conf import CONF
from cyborg.image.api import API as ImageAPI


LOG = logging.getLogger(__name__)


class AgentManager(periodic_task.PeriodicTasks):
    """Cyborg Agent manager main class.

    API version history:

    | 1.0 - Initial version.

    """

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

    def fpga_program(self, context, controlpath_id,
                     bitstream_uuid, driver_name):
        bitstream_uuid = str(bitstream_uuid)
        if not uuidutils.is_uuid_like(bitstream_uuid):
            raise exception.InvalidUUID(uuid=bitstream_uuid)
        download_path = tempfile.NamedTemporaryFile(suffix=".gbs",
                                                    prefix=bitstream_uuid)
        self.image_api.download(context,
                                bitstream_uuid,
                                dest_path=download_path.name)
        driver = self.fpga_driver.create(driver_name)
        ret = driver.program(controlpath_id, download_path.name)
        LOG.info('Driver program() API returned %s', ret)
        os.remove(download_path.name)
        return ret

    @periodic_task.periodic_task(run_immediately=True)
    def update_available_resource(self, context, startup=True):
        """Update all kinds of accelerator resources from their drivers."""
        self._rt.update_usage(context)
