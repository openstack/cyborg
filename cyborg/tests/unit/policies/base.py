# Copyright 2020 ZTE Corporation.
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

from oslo_log import log as logging
from oslo_utils.fixture import uuidsentinel as uuids

from cyborg import context as cyborg_context
from cyborg.tests.local_fixtures import policy_fixture
from cyborg.tests.unit.api.controllers.v2 import base as v2_test


LOG = logging.getLogger(__name__)

POLICY_DENY_EXPECTED = 'Bad response: 403 Forbidden'


class BasePolicyTest(v2_test.APITestV2):
    def setUp(self):
        super().setUp()
        self.policy = self.useFixture(policy_fixture.PolicyFixture())

        self.admin_project_id = uuids.admin_project_id
        self.project_id = uuids.project_id
        self.foo_project_id = uuids.foo_project_id
        self.project_id_other = uuids.project_id_other
        self.service_project_id = uuids.service_project_id

        # All test contexts include Keystone implied roles.
        # Implication chain: admin -> manager -> member -> reader.
        # The service role is separate (no implication).

        # legacy default role: "default:admin_or_owner"
        self.legacy_admin_context = cyborg_context.RequestContext(
            user_id="legacy_admin",
            project_id=self.admin_project_id,
            roles=['admin', 'manager', 'member', 'reader'],
        )
        self.legacy_owner_context = cyborg_context.RequestContext(
            user_id="legacy_owner",
            project_id=self.admin_project_id,
            roles=['member', 'reader'],
        )

        # system scoped users
        self.system_admin_context = cyborg_context.RequestContext(
            user_id="sys_admin",
            roles=['admin', 'manager', 'member', 'reader'],
            system_scope='all',
        )

        self.system_member_context = cyborg_context.RequestContext(
            user_id="sys_member",
            roles=['member', 'reader'],
            system_scope='all',
        )

        self.system_reader_context = cyborg_context.RequestContext(
            user_id="sys_reader",
            roles=['reader'],
            system_scope='all',
        )

        self.system_foo_context = cyborg_context.RequestContext(
            user_id="sys_foo",
            roles=['foo'],
            system_scope='all',
        )

        # project scoped users
        self.project_admin_context = cyborg_context.RequestContext(
            user_id="project_admin",
            project_id=self.project_id,
            roles=['admin', 'manager', 'member', 'reader'],
        )

        self.project_member_context = cyborg_context.RequestContext(
            user_id="project_member",
            project_id=self.project_id,
            roles=['member', 'reader'],
        )

        self.project_reader_context = cyborg_context.RequestContext(
            user_id="project_reader",
            project_id=self.project_id,
            roles=['reader'],
        )

        self.project_foo_context = cyborg_context.RequestContext(
            user_id="project_foo",
            project_id=self.project_id,
            roles=['foo'],
        )

        self.other_project_member_context = cyborg_context.RequestContext(
            user_id="other_project_member",
            project_id=self.project_id_other,
            roles=['member', 'reader'],
        )

        self.project_manager_context = cyborg_context.RequestContext(
            user_id="project_manager",
            project_id=self.project_id,
            roles=['manager', 'member', 'reader'],
        )

        self.project_service_context = cyborg_context.RequestContext(
            user_id="project_service",
            project_id=self.service_project_id,
            roles=['service'],
        )

        self.all_contexts = [
            self.legacy_admin_context,
            self.legacy_owner_context,
            self.system_admin_context,
            self.system_member_context,
            self.system_reader_context,
            self.system_foo_context,
            self.project_admin_context,
            self.project_member_context,
            self.project_reader_context,
            self.other_project_member_context,
            self.project_foo_context,
            self.project_manager_context,
            self.project_service_context,
        ]

    def set_enforce_new_defaults(self, value):
        self.flags(enforce_new_defaults=value, group='oslo_policy')
        self.policy.reset_enforcer()
