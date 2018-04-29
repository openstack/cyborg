# Copyright 2017 Lenovo, Inc.
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


"""
Cyborg Generic driver implementation.
"""

from cyborg.accelerator.drivers.modules import generic
from oslo_config import cfg
from oslo_log import log

from cyborg.accelerator import accelerator
from cyborg.conductor.rpcapi import ConductorAPI as conductor_api

LOG = log.getLogger(__name__)


CONF = cfg.CONF


class GenericDriver(generic.GENERICDRIVER):
    """Executes commands relating to Shares."""

    def __init__(self, *args, **kwargs):
        """Do initialization."""
        super(GenericDriver, self).__init__()
        self.configuration.append_config_values()
        self._helpers = {}
        self.backend_name = self.configuration.safe_get(
            'accelerator_backend_name')

    def do_setup(self, context):
        """Any initialization the generic driver does while starting."""
        super(GenericDriver, self).do_setup(context)
        self.acc = accelerator.Accelerator()

    def create_accelerator(self, context):
        """Creates accelerator."""
        self.acc = conductor_api.accelerator_create(
            context=context, obj_acc=self.accelerator)
        LOG.debug("Created a new accelerator with the UUID %s ",
                  self.accelerator.accelerator_id)

    def get_accelerator(self, context):
        """Gets accelerator by UUID."""
        self.acc = conductor_api.accelerator_list_one(
            context=context, obj_acc=self.accelerator)
        return self.acc

    def list_accelerators(self, context):
        """Lists all accelerators."""
        self.acc = conductor_api.accelerator_list_all(
            context=context, obj_acc=self.accelerator)
        return self.acc

    def update_accelerator(self, context):
        """Updates accelerator with a patch update."""

        self.acc = conductor_api.accelerator_update(
            context=context, obj_acc=self.accelerator)
        LOG.debug("Updated accelerator %s ",
                  self.accelerator.accelerator_id)

    def delete_accelerator(self, context):
        """Deletes a specific accelerator."""
        LOG.debug("Deleting accelerator %s ", self.accelerator.accelerator_id)
        conductor_api.accelerator_delete(context=context,
                                         obj_acc=self.accelerator)
