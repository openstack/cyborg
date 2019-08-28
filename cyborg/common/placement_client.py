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

from openstack import connection

from oslo_log import log as logging

from cyborg.conf import CONF

_CONN = None
LOG = logging.getLogger(__name__)


def get_placement():
    return _PlacementClient()


class _PlacementClient(object):

    def __init__(self):
        global _CONN
        if _CONN is None:
            default_user = 'devstack-admin'
            try:
                # TODO() CONF access fails.
                auth_user = CONF.placement.username or default_user
            except Exception:
                auth_user = default_user
            _CONN = connection.Connection(cloud=auth_user)
        self._client = _CONN.placement

    def _get_rp_traits(self, rp_uuid):
        placement = self._client
        resp = placement.get("/resource_providers/%s/traits" % rp_uuid,
                             microversion='1.6')
        if resp.status_code != 200:
            raise Exception(
                "Failed to get traits for rp %s: HTTP %d: %s" %
                (rp_uuid, resp.status_code, resp.text))
        return resp.json()

    def _ensure_traits(self, trait_names):
        placement = self._client
        for trait in trait_names:
            resp = placement.put('/traits/' + trait, microversion='1.6')
            if resp.status_code == 201:
                LOG.info("Created trait %(trait)s", {"trait": trait})
            elif resp.status_code == 204:
                LOG.info("Trait %(trait)s already existed", {"trait": trait})
            else:
                raise Exception(
                    "Failed to create trait %s: HTTP %d: %s" %
                    (trait, resp.status_code, resp.text))

    def _put_rp_traits(self, rp_uuid, traits_json):
        placement = self._client
        resp = placement.put("/resource_providers/%s/traits" % rp_uuid,
                             json=traits_json, microversion='1.6')
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
        LOG.info('Added traits %(traits)s to RP %(rp_uuid)s',
                 {"traits": traits, "rp_uuid": rp_uuid})

    def delete_traits_with_prefixes(self, rp_uuid, trait_prefixes):
        traits_json = self._get_rp_traits(rp_uuid)
        traits = [
            trait for trait in traits_json['traits']
            if not any(trait.startswith(prefix)
                       for prefix in trait_prefixes)]
        traits_json['traits'] = traits
        self._put_rp_traits(rp_uuid, traits_json)
        LOG.info('Deleted traits %(traits)s to RP %(rp_uuid)s',
                 {"traits": traits, "rp_uuid": rp_uuid})
