# Copyright (c) 2018 Huawei Technologies Co., Ltd
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

from unittest import mock

from keystoneauth1 import exceptions as ks_exc
from oslo_config import cfg
from oslo_utils import uuidutils

from cyborg.common import exception as c_exc
from cyborg.services import report as placement_client
from cyborg.tests import base


class PlacementAPIClientTestCase(base.DietTestCase):
    """Test the Placement API client."""

    def setUp(self):
        super(PlacementAPIClientTestCase, self).setUp()
        self.mock_load_auth_p = mock.patch(
            'keystoneauth1.loading.load_auth_from_conf_options')
        self.mock_load_auth = self.mock_load_auth_p.start()
        self.mock_request_p = mock.patch(
            'keystoneauth1.session.Session.request')
        self.mock_request = self.mock_request_p.start()
        self.client = placement_client.SchedulerReportClient()

    @mock.patch('keystoneauth1.session.Session')
    @mock.patch('keystoneauth1.loading.load_auth_from_conf_options')
    def test_constructor(self, load_auth_mock, ks_sess_mock):
        placement_client.SchedulerReportClient()

        load_auth_mock.assert_called_once_with(cfg.CONF, 'placement')
        ks_sess_mock.assert_called_once_with(auth=load_auth_mock.return_value,
                                             cert=None,
                                             collect_timing=False,
                                             split_loggers=False,
                                             timeout=None,
                                             verify=True)

    def test_create_resource_provider(self):
        expected_payload = 'fake_resource_provider'
        self.client.create_resource_provider(expected_payload)
        e_filter = {'region_name': mock.ANY, 'service_type': 'placement'}
        expected_url = '/resource_providers'
        self.mock_request.assert_called_once_with(expected_url, 'POST',
                                                  endpoint_filter=e_filter,
                                                  json=expected_payload)

    def test_delete_resource_provider(self):
        rp_uuid = uuidutils.generate_uuid()
        self.client.delete_resource_provider(rp_uuid)
        e_filter = {'region_name': mock.ANY, 'service_type': 'placement'}
        expected_url = '/resource_providers/%s' % rp_uuid
        self.mock_request.assert_called_once_with(expected_url, 'DELETE',
                                                  endpoint_filter=e_filter)

    def test_create_inventory(self):
        expected_payload = 'fake_inventory'
        rp_uuid = uuidutils.generate_uuid()
        e_filter = {'region_name': mock.ANY, 'service_type': 'placement'}
        self.client.create_inventory(rp_uuid, expected_payload)
        expected_url = '/resource_providers/%s/inventories' % rp_uuid
        self.mock_request.assert_called_once_with(expected_url, 'POST',
                                                  endpoint_filter=e_filter,
                                                  json=expected_payload)

    def test_get_inventory(self):
        rp_uuid = uuidutils.generate_uuid()
        e_filter = {'region_name': mock.ANY, 'service_type': 'placement'}
        resource_class = 'fake_resource_class'
        self.client.get_inventory(rp_uuid, resource_class)
        expected_url = '/resource_providers/%s/inventories/%s' % (
            rp_uuid, resource_class)
        self.mock_request.assert_called_once_with(expected_url, 'GET',
                                                  endpoint_filter=e_filter)

    def _test_get_inventory_not_found(self, details, expected_exception):
        rp_uuid = uuidutils.generate_uuid()
        resource_class = 'fake_resource_class'
        self.mock_request.side_effect = ks_exc.NotFound(details=details)
        self.assertRaises(expected_exception, self.client.get_inventory,
                          rp_uuid, resource_class)

    def test_get_inventory_not_found_no_resource_provider(self):
        self._test_get_inventory_not_found(
            "No resource provider with uuid",
            c_exc.PlacementResourceProviderNotFound)

    def test_get_inventory_not_found_no_inventory(self):
        self._test_get_inventory_not_found(
            "No inventory of class", c_exc.PlacementInventoryNotFound)

    def test_get_inventory_not_found_unknown_cause(self):
        self._test_get_inventory_not_found("Unknown cause", ks_exc.NotFound)

    def test_update_inventory(self):
        expected_payload = 'fake_inventory'
        rp_uuid = uuidutils.generate_uuid()
        e_filter = {'region_name': mock.ANY, 'service_type': 'placement'}
        resource_class = 'fake_resource_class'
        self.client.update_inventory(rp_uuid, expected_payload, resource_class)
        expected_url = '/resource_providers/%s/inventories/%s' % (
            rp_uuid, resource_class)
        self.mock_request.assert_called_once_with(expected_url, 'PUT',
                                                  endpoint_filter=e_filter,
                                                  json=expected_payload)

    def test_update_inventory_conflict(self):
        rp_uuid = uuidutils.generate_uuid()
        expected_payload = 'fake_inventory'
        resource_class = 'fake_resource_class'
        self.mock_request.side_effect = ks_exc.Conflict
        self.assertRaises(c_exc.PlacementInventoryUpdateConflict,
                          self.client.update_inventory, rp_uuid,
                          expected_payload, resource_class)
