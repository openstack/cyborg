# Copyright 2022 Inspur, Inc.
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
import fixtures
from unittest import mock

from cyborg.common import exception
from cyborg.common import placement_client
from cyborg.tests import base


class PlacementAPITest(base.TestCase):

    def setUp(self):
        super(PlacementAPITest, self).setUp()
        self.instance_uuid = '00000000-0000-0000-0000-000000000001'

        self.mock_sdk = self.useFixture(fixtures.MockPatch(
            'cyborg.common.utils.get_sdk_adapter')).mock.return_value
        self.mock_log_info = self.useFixture(fixtures.MockPatch(
            'cyborg.common.placement_client.LOG.info')).mock
        self.mock_log_debug = self.useFixture(fixtures.MockPatch(
            'cyborg.common.placement_client.LOG.debug')).mock

    def test_get(self):
        self.mock_sdk.get.return_value = mock.Mock(status_code=200)
        placement = placement_client.PlacementClient()
        placement.get(mock.Mock())
        msg = 'Successfully get resources from placement: %s'
        self.mock_log_debug.assert_called_once_with(msg, mock.ANY)

    def test_get_exception(self):
        placement = placement_client.PlacementClient()
        mock_ret = mock.Mock(status_code=500)
        self.mock_sdk.get.return_value = mock_ret
        self.assertRaises(exception.PlacementServerError,
                          placement.get, mock.Mock())

    def test_post(self):
        self.mock_sdk.post.return_value = mock.Mock(status_code=200)
        placement = placement_client.PlacementClient()
        placement.post(mock.Mock(), mock.ANY)
        msg = 'Successfully create resources from placement: %s'
        self.mock_log_debug.assert_called_once_with(msg, mock.ANY)

    def test_post_exception(self):
        placement = placement_client.PlacementClient()
        mock_ret = mock.Mock(status_code=500)
        self.mock_sdk.post.return_value = mock_ret
        self.assertRaises(exception.PlacementServerError,
                          placement.post, mock.Mock(), mock.ANY)

    def test_put(self):
        self.mock_sdk.put.return_value = mock.Mock(status_code=200)
        placement = placement_client.PlacementClient()
        placement.put(mock.Mock(), mock.ANY)
        msg = 'Successfully update resources from placement: %s'
        self.mock_log_debug.assert_called_once_with(msg, mock.ANY)

    def test_put_exception(self):
        placement = placement_client.PlacementClient()
        mock_ret = mock.Mock(status_code=500)
        self.mock_sdk.put.return_value = mock_ret
        self.assertRaises(exception.PlacementServerError,
                          placement.put, mock.Mock(), mock.ANY)

    def test_delete(self):
        self.mock_sdk.delete.return_value = mock.Mock(status_code=200)
        placement = placement_client.PlacementClient()
        placement.delete(mock.Mock(), mock.ANY)
        msg = 'Successfully delete resources from placement: %s'
        self.mock_log_debug.assert_called_once_with(msg, mock.ANY)

    def test_delete_exception(self):
        placement = placement_client.PlacementClient()
        mock_ret = mock.Mock(status_code=500)
        self.mock_sdk.delete.return_value = mock_ret
        self.assertRaises(exception.PlacementServerError,
                          placement.delete, mock.Mock(), mock.ANY)

    def test_get_rp_traits(self):
        self.mock_sdk.get.return_value = mock.Mock(status_code=200)
        placement = placement_client.PlacementClient()
        placement._get_rp_traits(mock.ANY)
        msg = 'Successfully get resources from placement: %s'
        self.mock_log_debug.assert_called_once_with(msg, mock.ANY)

    def test_get_rp_traits_exception(self):
        placement = placement_client.PlacementClient()
        mock_ret = mock.Mock(status_code=500)
        self.mock_sdk.get.return_value = mock_ret
        self.assertRaises(exception.PlacementServerError,
                          placement._get_rp_traits, mock.ANY)

    def test_ensure_traits(self):
        self.mock_sdk.put.return_value = mock.Mock(status_code=201)
        placement = placement_client.PlacementClient()
        self.mock_sdk.get.return_value = None
        placement._ensure_traits([mock.ANY])
        self.assertEqual(2, self.mock_log_debug.call_count)
        msg = 'Successfully update resources from placement: %s'
        # first call/arg
        self.assertIn(msg, self.mock_log_debug.call_args_list[1][0][0])

    def test_ensure_traits_exception(self):
        placement = placement_client.PlacementClient()
        mock_ret = mock.Mock(status_code=500)
        self.mock_sdk.get.return_value = None
        self.mock_sdk.put.return_value = mock_ret
        self.assertRaises(exception.PlacementServerError,
                          placement._ensure_traits, [mock.ANY])

    @mock.patch('cyborg.common.placement_client.'
                'PlacementClient.get_resource_provider')
    def test_put_rp_traits(self, rp):
        self.mock_sdk.put.return_value = mock.Mock(status_code=200)
        placement = placement_client.PlacementClient()
        rp.return_value = {'status_code': 200, 'generation': 0}
        placement._put_rp_traits(mock.ANY, {'traits': 'fake_trait'})
        msg = 'Successfully update resources from placement: %s'
        self.mock_log_debug.assert_called_once_with(msg, mock.ANY)

    @mock.patch('cyborg.common.placement_client.'
                'PlacementClient.get_resource_provider')
    def test_put_rp_traits_exception(self, rp):
        placement = placement_client.PlacementClient()
        mock_ret = mock.Mock(status_code=500)
        rp.return_value = {'status_code': 200, 'generation': 0}
        self.mock_sdk.put.return_value = mock_ret
        self.assertRaises(exception.PlacementServerError,
                          placement._put_rp_traits,
                          mock.ANY, {'traits': 'fake_trait'})
