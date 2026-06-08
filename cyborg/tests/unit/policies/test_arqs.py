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

import http

from unittest import mock

from cyborg.tests.unit import fake_device_profile
from cyborg.tests.unit import fake_extarq
from cyborg.tests.unit.policies import base


ARQ_URL = '/accelerator_requests'


class ARQPolicyTest(base.BasePolicyTest):
    """Test ARQ APIs policies with all possible contexts.

    This class defines the set of contexts with different roles
    which are allowed and not allowed to pass the policy checks.
    With those set of contexts, it will call the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super().setUp()
        self.fake_dp_obj = fake_device_profile.get_obj_devprofs()[1]
        self.fake_extarq_obj = fake_extarq.get_fake_extarq_objs()[0]

        # rule:project_member_or_admin with project scope enforced.
        # With enforce_new_defaults=False (Cyborg's default), oslo.policy
        # ORs the new check string with the deprecated bridge
        # (admin_or_owner: is_admin:True or project_id:%(project_id)s).
        # The request context is the policy target, so target project_id
        # equals the caller's project_id, meaning every project-scoped
        # context passes via the deprecated bridge. Only system-scoped
        # contexts are rejected (by enforce_scope=True).
        self.create_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
            self.legacy_owner_context,
            self.project_member_context,
            self.project_reader_context,
            self.other_project_member_context,
            self.project_foo_context,
            self.project_manager_context,
            self.project_service_context,
        ]
        self.create_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.create_authorized_contexts)
        )

    @mock.patch(
        'cyborg.conductor.rpcapi.ConductorAPI.arq_create', autospec=True
    )
    @mock.patch('cyborg.objects.DeviceProfile.get_by_name', autospec=True)
    def test_create_arq_success(self, mock_dp, mock_arq):
        mock_dp.return_value = self.fake_dp_obj
        mock_arq.return_value = self.fake_extarq_obj
        req_body = {'device_profile_name': self.fake_dp_obj.name}
        for context in self.create_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.post_json(ARQ_URL, req_body, headers=headers)
            self.assertEqual(http.HTTPStatus.CREATED, response.status_int)

    def test_create_arq_forbidden(self):
        req_body = {'device_profile_name': 'dp_example_1'}
        for context in self.create_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.post_json(ARQ_URL, req_body, headers=headers)

    @mock.patch('cyborg.objects.ExtARQ.list', autospec=True)
    def test_list_arq_system_scope_forbidden(self, mock_list):
        headers = self.gen_headers(self.system_admin_context)
        response = self.get_json(
            ARQ_URL, headers=headers, expect_errors=True, return_json=False
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_int)
        mock_list.assert_not_called()

    @mock.patch(
        'cyborg.conductor.rpcapi.ConductorAPI.arq_create', autospec=True
    )
    @mock.patch('cyborg.objects.DeviceProfile.get_by_name', autospec=True)
    def test_create_arq_system_scope_forbidden(self, mock_dp, mock_arq):
        headers = self.gen_headers(self.system_admin_context)
        with self.assertRaisesRegex(Exception, base.POLICY_DENY_EXPECTED):
            self.post_json(
                ARQ_URL,
                {'device_profile_name': 'dp_example_1'},
                headers=headers,
            )
        mock_dp.assert_not_called()
        mock_arq.assert_not_called()
