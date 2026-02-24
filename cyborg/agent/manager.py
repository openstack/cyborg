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
import time
import urllib.parse

from keystoneauth1 import exceptions as ks_exc
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import periodic_task
from oslo_utils import uuidutils

from cyborg.accelerator.drivers.fpga.base import FPGADriver
from cyborg.accelerator.drivers.gpu import utils as gpu_utils
from cyborg.agent.resource_tracker import ResourceTracker
from cyborg.agent.rpcapi import AgentAPI
from cyborg.common import exception
from cyborg.common import placement_client as placement
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
        self.host = host or CONF.host  # RPC server identity

        # TODO(cyborg): Long-term, the conductor should not be responsible
        # for creating resource providers in Placement. That responsibility
        # should be moved to the agent, similar to how nova-compute manages
        # its own resource provider.
        # See: https://bugs.launchpad.net/openstack-cyborg/+bug/2139369
        self.placement_client = placement.PlacementClient()

        # Validate and resolve the resource provider name at startup by
        # querying Placement. This ensures we use the correct hostname that
        # matches the Nova compute resource provider. Unlike self.host (used
        # for RPC), this name is used for Placement resource provider lookup.
        # Retry with exponential backoff to tolerate startup ordering when
        # nova-compute has not yet created the resource provider.
        retries = CONF.agent.resource_provider_startup_retries
        for attempt in range(retries + 1):
            try:
                self.resource_provider_name = (
                    self._get_resource_provider_name())
                break
            except exception.PlacementResourceProviderNotFound:
                if attempt < retries:
                    wait = 2 ** attempt  # 1, 2, 4, 8, ...
                    LOG.warning(
                        "Resource provider not found in Placement, "
                        "retrying in %(wait)ds (attempt %(attempt)d/"
                        "%(total)d)",
                        {'wait': wait,
                         'attempt': attempt + 1,
                         'total': retries + 1})
                    time.sleep(wait)
                else:
                    raise

        self.fpga_driver = FPGADriver()
        self.cond_api = cond_api.ConductorAPI()
        self.agent_api = AgentAPI()
        self.image_api = ImageAPI()
        self._rt = ResourceTracker(self.resource_provider_name, self.cond_api)

    def _get_resource_provider_name(self):
        """Determine the correct resource provider name by querying Placement.

        Tries CONF.agent.resource_provider_name (defaults to socket.getfqdn())
        first, then falls back to CONF.host. Aborts agent startup if neither
        hostname has a valid resource provider in Placement.

        :returns: The validated resource provider name.
        :raises PlacementResourceProviderNotFound: If no resource provider
            is found with either hostname.
        """
        primary = CONF.agent.resource_provider_name
        candidates = [primary]
        if CONF.host and CONF.host != primary:
            candidates.append(CONF.host)

        for candidate in candidates:
            if self._check_resource_provider_exists(candidate):
                if candidate != primary:
                    LOG.warning(
                        "Resource provider not found with name '%(primary)s', "
                        "using fallback '%(fallback)s'",
                        {'primary': primary, 'fallback': candidate})
                LOG.info("Using resource provider name: %s", candidate)
                return candidate

        LOG.error(
            "Could not find resource provider in Placement. Tried: %s. "
            "Ensure nova-compute is running and has registered with "
            "Placement, or set [agent] resource_provider_name to match "
            "the compute node's hypervisor_hostname.", candidates)
        raise exception.PlacementResourceProviderNotFound(
            resource_provider=primary)

    def _check_resource_provider_exists(self, hostname):
        """Check if a resource provider exists in Placement.

        :param hostname: The hostname to check.
        :returns: True if the resource provider exists, False otherwise.
        """
        try:
            resp = self.placement_client.get(
                "/resource_providers?name="
                + urllib.parse.quote(hostname))
            providers = resp.json().get("resource_providers", [])
            return len(providers) > 0
        except (ValueError, AttributeError) as e:
            LOG.warning(
                "Failed to parse Placement response for "
                "'%(name)s': %(err)s",
                {'name': hostname, 'err': e})
            return False
        except (ks_exc.ClientException,
                exception.PlacementServerError) as e:
            LOG.warning(
                "Failed to check resource provider '%(name)s': %(err)s",
                {'name': hostname, 'err': e})
            return False

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
        try:
            driver = self.fpga_driver.create(driver_name)
            ret = driver.program(controlpath_id, download_path.name)
            LOG.info('Driver program() API returned %s', ret)
        finally:
            LOG.debug('Remove tmp bitstream file: %s', download_path.name)
            os.remove(download_path.name)
        return ret

    @periodic_task.periodic_task(run_immediately=True)
    def update_available_resource(self, context, startup=True):
        """Update all kinds of accelerator resources from their drivers."""
        self._rt.update_usage(context)

    def create_vgpu_mdev(self, context, pci_addr, asked_type, ah_uuid):
        LOG.debug('Instantiate a mediated device')
        gpu_utils.create_mdev_privileged(pci_addr, asked_type, ah_uuid)

    def remove_vgpu_mdev(self, context, pci_addr, asked_type, ah_uuid):
        LOG.debug('Remove a vgpu mdev')
        gpu_utils.remove_mdev_privileged(pci_addr, asked_type, ah_uuid)
