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
from stevedore import driver
from stevedore.extension import ExtensionManager

from cyborg.common import exception
from cyborg.common import utils
from cyborg.conf import CONF


LOG = logging.getLogger(__name__)

AGENT_RESOURCE_SEMAPHORE = "agent_resources"


class ResourceTracker(object):
    """Agent helper class for keeping track of resource usage as instances
    are built and destroyed.
    """

    def __init__(self, host, cond_api):
        self.host = host
        self.conductor_api = cond_api
        self.acc_drivers = []
        self._initialize_drivers()

    def _initialize_drivers(self, enabled_drivers=None):
        """Load accelerator drivers.

        :return: [nvidia_gpu_driver_obj, intel_fpga_driver_obj]
        """
        acc_drivers = []
        if not enabled_drivers:
            enabled_drivers = CONF.agent.enabled_drivers
        valid_drivers = ExtensionManager(
            namespace='cyborg.accelerator.driver').names()
        for d in enabled_drivers:
            if d not in valid_drivers:
                raise exception.InvalidDriver(name=d)
            acc_driver = driver.DriverManager(
                namespace='cyborg.accelerator.driver', name=d,
                invoke_on_load=True).driver
            acc_drivers.append(acc_driver)
        self.acc_drivers = acc_drivers

    @utils.synchronized(AGENT_RESOURCE_SEMAPHORE)
    def update_usage(self, context):
        """Update the resource usage periodically.
        """
        acc_list = []
        for acc_driver in self.acc_drivers:
            acc_list.extend(acc_driver.discover())
        # Call conductor_api here to diff and report acc data. Now, we actually
        # do not have the method report_data.
        try:
            self.conductor_api.report_data(context, self.host, acc_list)
        except exception.PlacementResourceProviderNotFound as e:
            LOG.error('Unable to report usage: %s', e)
