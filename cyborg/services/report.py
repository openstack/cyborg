# Copyright (c) 2018 Huawei Technologies Co., Ltd
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

import functools

from keystoneauth1 import exceptions as k_exc
from keystoneauth1 import loading as k_loading
from oslo_config import cfg
from cyborg.common import exception as c_exc

from oslo_concurrency import lockutils

synchronized = lockutils.synchronized_with_prefix('cyborg-')

PLACEMENT_CLIENT_SEMAPHORE = 'placement_client'


def check_placement_api_available(f):
    @functools.wraps(f)
    def wrapper(self, *a, **k):
        try:
            return f(self, *a, **k)
        except k_exc.EndpointNotFound:
            raise c_exc.PlacementEndpointNotFound()
    return wrapper


class SchedulerReportClient(object):
    """Client class for updating the scheduler.

    This class is used for updating the placement DB on NOVA side
    Cyborg DB should be kept up to date with the placement DB all
    the time.

    Here is an example on how to use it:

    from cyborg.services import report as placement_report_client
    p_client = placement_report_client.SchedulerReportClient()

    resource_provider = {'name': 'rp_name', 'uuid': 'uuid'}
    p_client.create_resource_provider(resource_provider)

    """

    keystone_filter = {'service_type': 'placement',
                       'region_name': cfg.CONF.placement.region_name}

    def __init__(self):
        self.association_refresh_time = {}
        self._client = self._create_client()
        self._disabled = False

    def _create_client(self):
        """Create the HTTP session accessing the placement service."""
        self.association_refresh_time = {}
        auth_plugin = k_loading.load_auth_from_conf_options(
            cfg.CONF, 'placement')
        client = k_loading.load_session_from_conf_options(
            cfg.CONF, 'placement', auth=auth_plugin)
        client.additional_headers = {'accept': 'application/json'}
        return client

    def _get(self, url, **kwargs):
        return self._client.get(url, endpoint_filter=self.keystone_filter,
                                **kwargs)

    def _post(self, url, data, **kwargs):
        return self._client.post(url, json=data,
                                 endpoint_filter=self.keystone_filter,
                                 **kwargs)

    def _put(self, url, data, **kwargs):
        return self._client.put(url, json=data,
                                endpoint_filter=self.keystone_filter,
                                **kwargs)

    def _delete(self, url, **kwargs):
        return self._client.delete(url, endpoint_filter=self.keystone_filter,
                                   **kwargs)

    @check_placement_api_available
    def create_resource_provider(self, resource_provider):
        """Create a resource provider.

        :param resource_provider: The resource provider
        :type resource_provider: dict: name (required), uuid (required)
        """
        url = '/resource_providers'
        self._post(url, resource_provider)

    @check_placement_api_available
    def delete_resource_provider(self, resource_provider_uuid):
        """Delete a resource provider.

        :param resource_provider_uuid: UUID of the resource provider
        :type resource_provider_uuid: str
        """
        url = '/resource_providers/%s' % resource_provider_uuid
        self._delete(url)

    @check_placement_api_available
    def create_inventory(self, resource_provider_uuid, inventory):
        """Create an inventory.

        :param resource_provider_uuid: UUID of the resource provider
        :type resource_provider_uuid: str
        :param inventory: The inventory
        :type inventory: dict: resource_class (required), total (required),
          reserved (required), min_unit (required), max_unit (required),
          step_size (required), allocation_ratio (required)
        """
        url = '/resource_providers/%s/inventories' % resource_provider_uuid
        self._post(url, inventory)

    @check_placement_api_available
    def get_inventory(self, resource_provider_uuid, resource_class):
        """Get resource provider inventory.

        :param resource_provider_uuid: UUID of the resource provider
        :type resource_provider_uuid: str
        :param resource_class: Resource class name of the inventory to be
          returned
        :type resource_class: str
        :raises c_exc.PlacementInventoryNotFound: For failure to find inventory
          for a resource provider
        """
        url = '/resource_providers/%s/inventories/%s' % (
            resource_provider_uuid, resource_class)
        try:
            return self._get(url).json()
        except k_exc.NotFound as e:
            if "No resource provider with uuid" in e.details:
                raise c_exc.PlacementResourceProviderNotFound(
                    resource_provider=resource_provider_uuid)
            elif _("No inventory of class") in e.details:
                raise c_exc.PlacementInventoryNotFound(
                    resource_provider=resource_provider_uuid,
                    resource_class=resource_class)
            else:
                raise

    @check_placement_api_available
    def update_inventory(self, resource_provider_uuid, inventory,
                         resource_class):
        """Update an inventory.

        :param resource_provider_uuid: UUID of the resource provider
        :type resource_provider_uuid: str
        :param inventory: The inventory
        :type inventory: dict
        :param resource_class: The resource class of the inventory to update
        :type resource_class: str
        :raises c_exc.PlacementInventoryUpdateConflict: For failure to updste
          inventory due to outdated resource_provider_generation
        """
        url = '/resource_providers/%s/inventories/%s' % (
            resource_provider_uuid, resource_class)
        try:
            self._put(url, inventory)
        except k_exc.Conflict:
            raise c_exc.PlacementInventoryUpdateConflict(
                resource_provider=resource_provider_uuid,
                resource_class=resource_class)
