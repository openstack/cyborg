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

from cyborg.api.controllers.v2 import arqs
from cyborg.tests.unit import fake_device_profile
from cyborg.tests.unit import fake_extarq
from cyborg.tests.unit.policies import base


ARQ_URL = '/accelerator_requests'


class ARQPolicyTest(base.BasePolicyTest):
    """Test ARQ API policies with all possible contexts.

    Tests run with enforce_new_defaults=False (Cyborg's default), so
    deprecated bridges are active alongside the new check strings.

    ARQ policy checks use the request context as the policy target, so
    the policy target project_id always equals the caller's project_id.
    With the deprecated bridge (admin_or_owner: is_admin:True or
    project_id:%(project_id)s) active, every project-scoped context
    passes for read and write operations. Only system-scoped contexts
    are rejected by enforce_scope=True.
    """

    def setUp(self):
        super().setUp()
        self.fake_dp_obj = fake_device_profile.get_obj_devprofs()[1]
        self.fake_extarq_obj = fake_extarq.get_fake_extarq_objs()[0]
        self.arq_uuid = self.fake_extarq_obj.arq['uuid']
        self.patch_list = {
            self.arq_uuid: [{'path': '/hostname', 'op': 'remove'}]
        }

        # With enforce_new_defaults=False the deprecated bridge accepts
        # any project-scoped context. All project-scoped contexts are
        # authorized; only system-scoped contexts are rejected.
        self.read_authorized_contexts = [
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
        self.read_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.read_authorized_contexts)
        )

        # Same reasoning applies to write operations. Keep independent
        # collections so future read/write policy changes remain explicit.
        self.write_authorized_contexts = list(self.read_authorized_contexts)
        self.write_unauthorized_contexts = list(
            self.read_unauthorized_contexts
        )

    @mock.patch('cyborg.objects.ExtARQ.list', autospec=True)
    def test_get_all_arqs_success(self, mock_list):
        mock_list.return_value = [self.fake_extarq_obj]
        for context in self.read_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    ARQ_URL, headers=headers, return_json=False
                )
                self.assertEqual(http.HTTPStatus.OK, response.status_int)

    def test_get_all_arqs_forbidden(self):
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    ARQ_URL,
                    headers=headers,
                    expect_errors=True,
                    return_json=False,
                )
                self.assertEqual(
                    http.HTTPStatus.FORBIDDEN, response.status_int
                )

    @mock.patch('cyborg.objects.ExtARQ.list', autospec=True)
    def test_list_arq_system_scope_forbidden(self, mock_list):
        headers = self.gen_headers(self.system_admin_context)
        response = self.get_json(
            ARQ_URL, headers=headers, expect_errors=True, return_json=False
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_int)
        mock_list.assert_not_called()

    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    def test_get_one_arq_success(self, mock_get):
        mock_get.return_value = self.fake_extarq_obj
        url = f'{ARQ_URL}/{self.arq_uuid}'
        for context in self.read_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    url, headers=headers, return_json=False
                )
                self.assertEqual(http.HTTPStatus.OK, response.status_int)

    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    def test_get_one_arq_forbidden(self, mock_get):
        url = f'{ARQ_URL}/{self.arq_uuid}'
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    url,
                    headers=headers,
                    expect_errors=True,
                    return_json=False,
                )
                self.assertEqual(
                    http.HTTPStatus.FORBIDDEN, response.status_int
                )
        mock_get.assert_not_called()

    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    def test_get_one_arq_system_scope_forbidden(self, mock_get):
        headers = self.gen_headers(self.system_admin_context)
        response = self.get_json(
            f'{ARQ_URL}/{self.arq_uuid}',
            headers=headers,
            expect_errors=True,
            return_json=False,
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_int)
        mock_get.assert_not_called()

    @mock.patch('cyborg.objects.ExtARQ.delete_by_uuid', autospec=True)
    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._check_bound_arq_service_token',
        autospec=True,
    )
    def test_delete_arq_success(self, mock_check, mock_get, mock_delete):
        mock_get.return_value = self.fake_extarq_obj
        url = f'{ARQ_URL}?arqs={self.arq_uuid}'
        for context in self.write_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.delete(url, headers=headers)
                self.assertEqual(
                    http.HTTPStatus.NO_CONTENT, response.status_int
                )

    @mock.patch('cyborg.objects.ExtARQ.delete_by_uuid', autospec=True)
    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._check_bound_arq_service_token',
        autospec=True,
    )
    def test_delete_arq_forbidden(self, mock_check, mock_get, mock_delete):
        url = f'{ARQ_URL}?arqs={self.arq_uuid}'
        for context in self.write_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.delete(
                    url, headers=headers, expect_errors=True
                )
                self.assertEqual(
                    http.HTTPStatus.FORBIDDEN, response.status_int
                )
        mock_check.assert_not_called()
        mock_get.assert_not_called()
        mock_delete.assert_not_called()

    @mock.patch('cyborg.objects.ExtARQ.delete_by_uuid', autospec=True)
    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._check_bound_arq_service_token',
        autospec=True,
    )
    def test_delete_arq_system_scope_forbidden(
        self, mock_check, mock_get, mock_delete
    ):
        response = self.delete(
            f'{ARQ_URL}?arqs={self.arq_uuid}',
            headers=self.gen_headers(self.system_admin_context),
            expect_errors=True,
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_int)
        mock_check.assert_not_called()
        mock_get.assert_not_called()
        mock_delete.assert_not_called()

    @mock.patch(
        'cyborg.conductor.rpcapi.ConductorAPI.arq_apply_patch', autospec=True
    )
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._require_service_token', autospec=True
    )
    @mock.patch.object(
        arqs.ARQsController, '_validate_arq_patch', autospec=True
    )
    def test_update_arq_success(
        self, mock_validate, mock_require_service, mock_apply
    ):
        mock_validate.return_value = {
            'hostname': None,
            'device_rp_uuid': None,
            'instance_uuid': None,
        }
        for context in self.write_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.patch_json(
                    ARQ_URL, params=self.patch_list, headers=headers
                )
                self.assertEqual(http.HTTPStatus.ACCEPTED, response.status_int)

    @mock.patch(
        'cyborg.conductor.rpcapi.ConductorAPI.arq_apply_patch', autospec=True
    )
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._require_service_token', autospec=True
    )
    @mock.patch.object(
        arqs.ARQsController, '_validate_arq_patch', autospec=True
    )
    def test_update_arq_forbidden(
        self, mock_validate, mock_require_service, mock_apply
    ):
        for context in self.write_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.patch_json(
                    ARQ_URL,
                    params=self.patch_list,
                    headers=headers,
                    expect_errors=True,
                )
                self.assertEqual(
                    http.HTTPStatus.FORBIDDEN, response.status_int
                )
        mock_validate.assert_not_called()
        mock_require_service.assert_not_called()
        mock_apply.assert_not_called()

    @mock.patch(
        'cyborg.conductor.rpcapi.ConductorAPI.arq_apply_patch', autospec=True
    )
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._require_service_token', autospec=True
    )
    @mock.patch.object(
        arqs.ARQsController, '_validate_arq_patch', autospec=True
    )
    def test_update_arq_system_scope_forbidden(
        self, mock_validate, mock_require_service, mock_apply
    ):
        response = self.patch_json(
            ARQ_URL,
            params=self.patch_list,
            headers=self.gen_headers(self.system_admin_context),
            expect_errors=True,
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_int)
        mock_validate.assert_not_called()
        mock_require_service.assert_not_called()
        mock_apply.assert_not_called()

    @mock.patch(
        'cyborg.conductor.rpcapi.ConductorAPI.arq_create', autospec=True
    )
    @mock.patch('cyborg.objects.DeviceProfile.get_by_name', autospec=True)
    def test_create_arq_success(self, mock_dp, mock_arq):
        mock_dp.return_value = self.fake_dp_obj
        mock_arq.return_value = self.fake_extarq_obj
        req_body = {'device_profile_name': self.fake_dp_obj.name}
        for context in self.write_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.post_json(ARQ_URL, req_body, headers=headers)
                self.assertEqual(http.HTTPStatus.CREATED, response.status_int)

    def test_create_arq_forbidden(self):
        req_body = {'device_profile_name': 'dp_example_1'}
        for context in self.write_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.post_json(ARQ_URL, req_body, headers=headers)

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


class ARQPolicyNewDefaultsTest(base.BasePolicyTest):
    """Test ARQ API policies with enforce_new_defaults=True.

    With new defaults enforced, only the new check strings apply;
    deprecated bridges are inactive.

    Read operations use project_reader_or_admin:
      rule:project_reader_api or rule:admin_api
    Write operations use project_member_or_service:
      rule:project_member_api or rule:service_api

    ARQ policy checks use the request context as the policy target, so
    the target project_id always equals the caller's own project_id.
    Role implication (admin->member->reader) is NOT applied
    in unit tests; each context carries its Keystone implied roles.
    """

    def setUp(self):
        super().setUp()
        self.set_enforce_new_defaults(True)
        self.fake_dp_obj = fake_device_profile.get_obj_devprofs()[1]
        self.fake_extarq_obj = fake_extarq.get_fake_extarq_objs()[0]
        self.arq_uuid = self.fake_extarq_obj.arq['uuid']
        self.patch_list = {
            self.arq_uuid: [{'path': '/hostname', 'op': 'remove'}]
        }

        # project_reader_or_admin:
        # (role:reader and project_id) or role:admin.
        # With implied roles, admin/manager/member all carry reader,
        # so every project-scoped context with a standard role passes
        # except service and foo.
        self.read_authorized_contexts = [
            self.legacy_admin_context,
            self.legacy_owner_context,
            self.project_admin_context,
            self.project_manager_context,
            self.project_member_context,
            self.project_reader_context,
            self.other_project_member_context,
        ]
        self.read_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.read_authorized_contexts)
        )

        # project_member_or_service:
        # (role:member and project_id) or role:service.
        # With implied roles, admin and manager carry member,
        # so they also pass.
        self.write_authorized_contexts = [
            self.legacy_admin_context,
            self.legacy_owner_context,
            self.project_admin_context,
            self.project_manager_context,
            self.project_member_context,
            self.other_project_member_context,
            self.project_service_context,
        ]
        self.write_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.write_authorized_contexts)
        )

    @mock.patch('cyborg.objects.ExtARQ.list', autospec=True)
    def test_get_all_arqs_new_defaults_success(self, mock_list):
        mock_list.return_value = [self.fake_extarq_obj]
        for context in self.read_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    ARQ_URL, headers=headers, return_json=False
                )
                self.assertEqual(http.HTTPStatus.OK, response.status_int)

    def test_get_all_arqs_new_defaults_forbidden(self):
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    ARQ_URL,
                    headers=headers,
                    expect_errors=True,
                    return_json=False,
                )
                self.assertEqual(
                    http.HTTPStatus.FORBIDDEN, response.status_int
                )

    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    def test_get_one_arq_new_defaults_success(self, mock_get):
        mock_get.return_value = self.fake_extarq_obj
        url = f'{ARQ_URL}/{self.arq_uuid}'
        for context in self.read_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    url, headers=headers, return_json=False
                )
                self.assertEqual(http.HTTPStatus.OK, response.status_int)

    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    def test_get_one_arq_new_defaults_forbidden(self, mock_get):
        url = f'{ARQ_URL}/{self.arq_uuid}'
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    url,
                    headers=headers,
                    expect_errors=True,
                    return_json=False,
                )
                self.assertEqual(
                    http.HTTPStatus.FORBIDDEN, response.status_int
                )
        mock_get.assert_not_called()

    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    def test_get_one_arq_new_defaults_service_forbidden(self, mock_get):
        response = self.get_json(
            f'{ARQ_URL}/{self.arq_uuid}',
            headers=self.gen_headers(self.project_service_context),
            expect_errors=True,
            return_json=False,
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_int)
        mock_get.assert_not_called()

    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    def test_get_one_arq_new_defaults_system_scope_forbidden(self, mock_get):
        response = self.get_json(
            f'{ARQ_URL}/{self.arq_uuid}',
            headers=self.gen_headers(self.system_admin_context),
            expect_errors=True,
            return_json=False,
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_int)
        mock_get.assert_not_called()

    @mock.patch('cyborg.objects.ExtARQ.delete_by_uuid', autospec=True)
    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._check_bound_arq_service_token',
        autospec=True,
    )
    def test_delete_arq_new_defaults_success(
        self, mock_check, mock_get, mock_delete
    ):
        mock_get.return_value = self.fake_extarq_obj
        self.assertIn(
            self.project_service_context, self.write_authorized_contexts
        )
        url = f'{ARQ_URL}?arqs={self.arq_uuid}'
        for context in self.write_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.delete(url, headers=headers)
                self.assertEqual(
                    http.HTTPStatus.NO_CONTENT, response.status_int
                )

    @mock.patch('cyborg.objects.ExtARQ.delete_by_uuid', autospec=True)
    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._check_bound_arq_service_token',
        autospec=True,
    )
    def test_delete_arq_new_defaults_forbidden(
        self, mock_check, mock_get, mock_delete
    ):
        url = f'{ARQ_URL}?arqs={self.arq_uuid}'
        for context in self.write_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.delete(
                    url, headers=headers, expect_errors=True
                )
                self.assertEqual(
                    http.HTTPStatus.FORBIDDEN, response.status_int
                )
        mock_check.assert_not_called()
        mock_get.assert_not_called()
        mock_delete.assert_not_called()

    @mock.patch('cyborg.objects.ExtARQ.delete_by_uuid', autospec=True)
    @mock.patch('cyborg.objects.ExtARQ.get', autospec=True)
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._check_bound_arq_service_token',
        autospec=True,
    )
    def test_delete_arq_new_defaults_system_scope_forbidden(
        self, mock_check, mock_get, mock_delete
    ):
        response = self.delete(
            f'{ARQ_URL}?arqs={self.arq_uuid}',
            headers=self.gen_headers(self.system_admin_context),
            expect_errors=True,
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_int)
        mock_check.assert_not_called()
        mock_get.assert_not_called()
        mock_delete.assert_not_called()

    @mock.patch(
        'cyborg.conductor.rpcapi.ConductorAPI.arq_apply_patch', autospec=True
    )
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._require_service_token', autospec=True
    )
    @mock.patch.object(
        arqs.ARQsController, '_validate_arq_patch', autospec=True
    )
    def test_update_arq_new_defaults_success(
        self, mock_validate, mock_require_service, mock_apply
    ):
        mock_validate.return_value = {
            'hostname': None,
            'device_rp_uuid': None,
            'instance_uuid': None,
        }
        self.assertIn(
            self.project_service_context, self.write_authorized_contexts
        )
        for context in self.write_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.patch_json(
                    ARQ_URL, params=self.patch_list, headers=headers
                )
                self.assertEqual(http.HTTPStatus.ACCEPTED, response.status_int)

    @mock.patch(
        'cyborg.conductor.rpcapi.ConductorAPI.arq_apply_patch', autospec=True
    )
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._require_service_token', autospec=True
    )
    @mock.patch.object(
        arqs.ARQsController, '_validate_arq_patch', autospec=True
    )
    def test_update_arq_new_defaults_forbidden(
        self, mock_validate, mock_require_service, mock_apply
    ):
        for context in self.write_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.patch_json(
                    ARQ_URL,
                    params=self.patch_list,
                    headers=headers,
                    expect_errors=True,
                )
                self.assertEqual(
                    http.HTTPStatus.FORBIDDEN, response.status_int
                )
        mock_validate.assert_not_called()
        mock_require_service.assert_not_called()
        mock_apply.assert_not_called()

    @mock.patch(
        'cyborg.conductor.rpcapi.ConductorAPI.arq_apply_patch', autospec=True
    )
    @mock.patch(
        'cyborg.api.controllers.v2.arqs._require_service_token', autospec=True
    )
    @mock.patch.object(
        arqs.ARQsController, '_validate_arq_patch', autospec=True
    )
    def test_update_arq_new_defaults_system_scope_forbidden(
        self, mock_validate, mock_require_service, mock_apply
    ):
        response = self.patch_json(
            ARQ_URL,
            params=self.patch_list,
            headers=self.gen_headers(self.system_admin_context),
            expect_errors=True,
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_int)
        mock_validate.assert_not_called()
        mock_require_service.assert_not_called()
        mock_apply.assert_not_called()

    @mock.patch(
        'cyborg.conductor.rpcapi.ConductorAPI.arq_create', autospec=True
    )
    @mock.patch('cyborg.objects.DeviceProfile.get_by_name', autospec=True)
    def test_create_arq_new_defaults_success(self, mock_dp, mock_arq):
        mock_dp.return_value = self.fake_dp_obj
        mock_arq.return_value = self.fake_extarq_obj
        req_body = {'device_profile_name': self.fake_dp_obj.name}
        for context in self.write_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.post_json(ARQ_URL, req_body, headers=headers)
                self.assertEqual(http.HTTPStatus.CREATED, response.status_int)

    def test_create_arq_new_defaults_forbidden(self):
        req_body = {'device_profile_name': 'dp_example_1'}
        for context in self.write_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.post_json(ARQ_URL, req_body, headers=headers)
