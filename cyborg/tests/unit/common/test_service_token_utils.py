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

"""Tests for service token validation utilities."""

from unittest import mock

from oslo_config import cfg

from cyborg.common import service_token_utils
from cyborg.tests import base


CONF = cfg.CONF


class TestIsServiceRequest(base.TestCase):
    """Tests for is_service_request() helper."""

    def _make_context(self, service_roles=None):
        ctx = mock.MagicMock()
        ctx.service_roles = service_roles or []
        return ctx

    def test_with_service_role(self):
        ctx = self._make_context(service_roles=['service'])
        self.assertTrue(service_token_utils.is_service_request(ctx))

    def test_without_service_token(self):
        ctx = self._make_context(service_roles=[])
        self.assertFalse(service_token_utils.is_service_request(ctx))

    def test_with_none_service_roles(self):
        ctx = self._make_context(service_roles=None)
        self.assertFalse(service_token_utils.is_service_request(ctx))

    def test_with_wrong_role(self):
        ctx = self._make_context(service_roles=['member'])
        self.assertFalse(service_token_utils.is_service_request(ctx))

    def test_with_multiple_roles_including_service(self):
        ctx = self._make_context(service_roles=['admin', 'service'])
        self.assertTrue(service_token_utils.is_service_request(ctx))

    def test_with_custom_config(self):
        CONF.set_override(
            'service_token_roles', ['custom_role'], group='keystone_authtoken'
        )
        ctx = self._make_context(service_roles=['custom_role'])
        self.assertTrue(service_token_utils.is_service_request(ctx))

    def test_custom_config_no_match(self):
        CONF.set_override(
            'service_token_roles', ['custom_role'], group='keystone_authtoken'
        )
        ctx = self._make_context(service_roles=['service'])
        self.assertFalse(service_token_utils.is_service_request(ctx))
