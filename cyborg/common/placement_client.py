# Copyright 2019 Intel, Inc.
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

from cyborg.common import exception
from cyborg.common import utils
from keystoneauth1 import exceptions as ks_exc
import os_resource_classes as orc
from oslo_log import log as logging
from oslo_middleware import request_id


LOG = logging.getLogger(__name__)
NESTED_PROVIDER_API_VERSION = '1.14'
POST_RPS_RETURNS_PAYLOAD_API_VERSION = '1.20'
PLACEMENT_CLIENT_SEMAPHORE = 'placement_client'


class PlacementClient(object):
    """Client class for reporting to placement."""

    def __init__(self):
        self._client = utils.get_sdk_adapter('placement')

    def get(self, url, version=None, global_request_id=None):
        res = self._client.get(url, microversion=version,
                               global_request_id=global_request_id)
        if res.status_code >= 500:
            raise exception.PlacementServerError(
                "Placement Server has some error at this time.")
        return res

    def post(self, url, data, version=None, global_request_id=None):
        res = self._client.post(url, json=data, microversion=version,
                                global_request_id=global_request_id)
        if res.status_code >= 500:
            raise exception.PlacementServerError(
                "Placement Server has some error at this time.")
        return res

    def put(self, url, data, version=None, global_request_id=None):
        kwargs = {}
        if data is not None:
            kwargs['json'] = data
        res = self._client.put(url, microversion=version,
                               global_request_id=global_request_id,
                               **kwargs)
        if res.status_code >= 500:
            raise exception.PlacementServerError(
                "Placement Server has some error at this time.")
        return res

    def delete(self, url, version=None, global_request_id=None):
        res = self._client.delete(url, microversion=version,
                                  global_request_id=global_request_id)
        if res.status_code >= 500:
            raise exception.PlacementServerError(
                "Placement Server has some error at this time.")
        return res

    def _get_rp_traits(self, rp_uuid):
        resp = self.get("/resource_providers/%s/traits" % rp_uuid,
                        version='1.6')
        if resp.status_code != 200:
            raise Exception(
                "Failed to get traits for rp %s: HTTP %d: %s" %
                (rp_uuid, resp.status_code, resp.text))
        return resp.json()

    def _ensure_traits(self, trait_names):
        # TODO(Xinran): maintain a reference count of how many RPs use
        # this trait and do the deletion only when the last RP is deleted.
        for trait in trait_names:
            resp = self.put("/traits/%s" % trait, None, version='1.6')
            if resp.status_code == 201:
                LOG.info("Created trait %(trait)s", {"trait": trait})
            elif resp.status_code == 204:
                LOG.info("Trait %(trait)s already existed", {"trait": trait})
            else:
                raise Exception(
                    "Failed to create trait %s: HTTP %d: %s" %
                    (trait, resp.status_code, resp.text))

    def _put_rp_traits(self, rp_uuid, traits_json):
        generation = self.get_resource_provider(
            resource_provider_uuid=rp_uuid)['generation']
        payload = {
            'resource_provider_generation': generation,
            'traits': traits_json["traits"],
        }
        resp = self.put(
            "/resource_providers/%s/traits" % rp_uuid, payload, version='1.6')
        if resp.status_code != 200:
            raise Exception(
                "Failed to set traits to %s for rp %s: HTTP %d: %s" %
                (traits_json, rp_uuid, resp.status_code, resp.text))

    def add_traits_to_rp(self, rp_uuid, trait_names):
        self._ensure_traits(trait_names)
        traits_json = self._get_rp_traits(rp_uuid)
        traits = list(set(traits_json['traits'] + trait_names))
        traits_json['traits'] = traits
        self._put_rp_traits(rp_uuid, traits_json)

    def delete_trait_by_name(self, rp_uuid, trait_name):
        traits_json = self._get_rp_traits(rp_uuid)
        traits = [
            trait for trait in traits_json['traits']
            if trait != trait_name
            ]
        traits_json['traits'] = traits
        self._put_rp_traits(rp_uuid, traits_json)

    def delete_traits_with_prefixes(self, rp_uuid, trait_prefixes):
        traits_json = self._get_rp_traits(rp_uuid)
        traits = [
            trait for trait in traits_json['traits']
            if not any(trait.startswith(prefix)
                       for prefix in trait_prefixes)]
        traits_json['traits'] = traits
        self._put_rp_traits(rp_uuid, traits_json)

    def get_placement_request_id(self, response):
        if response is not None:
            return response.headers.get(request_id.HTTP_RESP_HEADER_REQUEST_ID)

    def update_inventory(
            self, resource_provider_uuid, inventories,
            resource_provider_generation=None):
        if resource_provider_generation is None:
            resource_provider_generation = self.get_resource_provider(
                resource_provider_uuid=resource_provider_uuid)['generation']
        url = '/resource_providers/%s/inventories' % resource_provider_uuid
        body = {
            'resource_provider_generation': resource_provider_generation,
            'inventories': inventories
        }
        try:
            return self.put(url, body).json()
        except ks_exc.NotFound:
            raise exception.PlacementResourceProviderNotFound(
                resource_provider=resource_provider_uuid)

    def get_resource_provider(self, resource_provider_uuid):
        """Get resource provider by UUID.

        :param resource_provider_uuid: UUID of the resource provider.
        :raises PlacementResourceProviderNotFound: For failure to find resource
        :returns: The Resource Provider matching the UUID.
        """
        url = '/resource_providers/%s' % resource_provider_uuid
        try:
            return self.get(url).json()
        except ks_exc.NotFound:
            raise exception.PlacementResourceProviderNotFound(
                resource_provider=resource_provider_uuid)

    def _create_resource_provider(self, context, uuid, name,
                                  parent_provider_uuid=None):
        """Calls the placement API to create a new resource provider record.

        :param context: The security context
        :param uuid: UUID of the new resource provider
        :param name: Name of the resource provider
        :param parent_provider_uuid: Optional UUID of the immediate parent
        :return: A dict of resource provider information object representing
                 the newly-created resource provider.
        :raise: ResourceProviderCreationFailed or
                ResourceProviderRetrievalFailed on error.
        """
        url = "/resource_providers"
        payload = {
            'uuid': uuid,
            'name': name,
        }
        if parent_provider_uuid is not None:
            payload['parent_provider_uuid'] = parent_provider_uuid

        # Bug #1746075: First try the microversion that returns the new
        # provider's payload.
        resp = self.post(url, payload,
                         version=POST_RPS_RETURNS_PAYLOAD_API_VERSION,
                         global_request_id=context.global_id)

        placement_req_id = self.get_placement_request_id(resp)

        if resp:
            msg = ("[%(placement_req_id)s] Created resource provider record "
                   "via placement API for resource provider with UUID "
                   "%(uuid)s and name %(name)s.")
            args = {
                'uuid': uuid,
                'name': name,
                'placement_req_id': placement_req_id,
            }
            LOG.info(msg, args)
            return resp.json()

    def ensure_resource_provider(self, context, uuid, name=None,
                                 parent_provider_uuid=None):
        resp = self.get("/resource_providers/%s" % uuid, version='1.6')
        if resp.status_code == 200:
            LOG.info("Resource Provider %(uuid)s already exists",
                     {"uuid": uuid})
        else:
            LOG.info("Creating resource provider %(provider)s",
                     {"provider": name or uuid})
            try:
                resp = self._create_resource_provider(context, uuid, name,
                                                      parent_provider_uuid)
            except Exception:
                raise exception.ResourceProviderCreationFailed(
                    name=name or uuid)
        return uuid

    def ensure_resource_classes(self, context, names):
        """Make sure resource classes exist."""
        version = '1.7'
        to_ensure = set(names)
        for name in to_ensure:
            # no payload on the put request
            # if rc exists in placement's db, skip it.
            if name in orc.STANDARDS:
                return
            resp = self.put(
                "/resource_classes/%s" % name, None, version=version,
                global_request_id=context.global_id)
            if not resp:
                msg = ("Failed to ensure resource class record with placement "
                       "API for resource class %(rc_name)s. Got "
                       "%(status_code)d: %(err_text)s.")
                args = {
                    'rc_name': name,
                    'status_code': resp.status_code,
                    'err_text': resp.text,
                }
                LOG.error(msg, args)
                raise exception.InvalidResourceClass(resource_class=name)
            elif resp.status_code == 204:
                LOG.info("Resource class  %(rc_name)s already exists",
                         {"rc_name": name})
            elif resp.status_code == 201:
                LOG.info("Successfully created resource class %(rc_name).", {
                         "rc_name", name})

    def get_providers_in_tree(self, context, uuid):
        """Queries the placement API for a list of the resource providers in
        the tree associated with the specified UUID.

        :param context: The security context
        :param uuid: UUID identifier for the resource provider to look up
        :return: A list of dicts of resource provider information, which may be
                 empty if no provider exists with the specified UUID.
        :raise: ResourceProviderRetrievalFailed on error.
        """
        resp = self.get("/resource_providers?in_tree=%s" % uuid,
                        version=NESTED_PROVIDER_API_VERSION,
                        global_request_id=context.global_id)

        if resp.status_code == 200:
            return resp.json()['resource_providers']

        # Some unexpected error
        placement_req_id = self.get_placement_request_id(resp)
        msg = ("[%(placement_req_id)s] Failed to retrieve resource provider "
               "tree from placement API for UUID %(uuid)s. Got "
               "%(status_code)d: %(err_text)s.")
        args = {
            'uuid': uuid,
            'status_code': resp.status_code,
            'err_text': resp.text,
            'placement_req_id': placement_req_id,
        }
        LOG.error(msg, args)
        raise exception.ResourceProviderRetrievalFailed(uuid=uuid)

    def delete_provider(self, rp_uuid, global_request_id=None):
        resp = self.delete('/resource_providers/%s' % rp_uuid,
                           global_request_id=global_request_id)
        # Check for 404 since we don't need to warn/raise if we tried to delete
        # something which doesn"t actually exist.
        if resp.ok:
            LOG.info("Deleted resource provider %s", rp_uuid)
            return

        msg = ("[%(placement_req_id)s] Failed to delete resource provider "
               "with UUID %(uuid)s from the placement API. Got "
               "%(status_code)d: %(err_text)s.")
        args = {
            'placement_req_id': self.get_placement_request_id(resp),
            'uuid': rp_uuid,
            'status_code': resp.status_code,
            'err_text': resp.text
        }
        LOG.error(msg, args)
        # On conflict, the caller may wish to delete allocations and
        # redrive.  (Note that this is not the same as a
        # PlacementAPIConflict case.)
        if resp.status_code == 409:
            raise exception.ResourceProviderInUse()
        raise exception.ResourceProviderDeletionFailed(uuid=rp_uuid)
