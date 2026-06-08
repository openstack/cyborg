# Copyright 2026 Red Hat, Inc.
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

from cyborg import context as cyborg_context
from cyborg.tests.unit.api import base


class TestBaseApiTest(base.BaseApiTest):
    def test_gen_headers_preserves_explicit_empty_roles(self):
        headers = self.gen_headers(self.context, roles=[])

        self.assertEqual('', headers['X-Roles'])

    def test_gen_headers_uses_fallback_for_none_roles(self):
        admin_headers = self.gen_headers(self.context, roles=None)
        user_context = cyborg_context.RequestContext(is_admin=False)
        user_headers = self.gen_headers(user_context, roles=None)

        self.assertEqual('admin', admin_headers['X-Roles'])
        self.assertEqual('user', user_headers['X-Roles'])

    def test_gen_headers_joins_role_list(self):
        headers = self.gen_headers(
            self.context, roles=['admin', 'manager', 'member', 'reader']
        )

        self.assertEqual('admin,manager,member,reader', headers['X-Roles'])
