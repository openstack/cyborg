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

from cyborg.tests.unit import fake_attribute
from cyborg.tests.unit.policies import base


ATTRIBUTE_URL = '/attributes'


class AttributePolicyTest(base.BasePolicyTest):
    """Test attribute APIs policies with all possible contexts.

    This class defines the set of contexts with different roles
    which are allowed and not allowed to pass the policy checks.
    With those set of contexts, it will call the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super().setUp()
        self.fake_attr_obj = fake_attribute.fake_attribute_obj(self.context)
        self.fake_attr_dict = fake_attribute.fake_db_attribute()

        # Policy checks use the request context as target, so target
        # project_id equals the caller's project_id. Under
        # enforce_new_defaults=False oslo.policy ORs the new endpoint
        # check (project_manager_or_admin) with the deprecated bridge
        # (admin_api), AND also ORs the base rule
        # project_manager_or_admin's own deprecated bridge
        # (DEPRECATED_ADMIN_OR_OWNER: is_admin:True or
        # project_id:%(project_id)s). The project_id:%(project_id)s
        # branch therefore matches every project-scoped context. Only
        # system-scoped contexts are rejected by enforce_scope=True.
        self.read_all_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
            self.legacy_owner_context,
            self.project_member_context,
            self.project_reader_context,
            self.project_foo_context,
            self.other_project_member_context,
            self.project_manager_context,
            self.project_service_context,
        ]
        self.read_all_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.read_all_authorized_contexts)
        )

        # get_one follows the same widening pattern as get_all.
        # The legacy and new checks for create and delete are both
        # admin_api, so they are admin-only in both modes. The
        # request-context target is irrelevant because admin_api has no
        # project_id requirement.
        self.admin_only_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
        ]
        self.admin_only_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.admin_only_authorized_contexts)
        )

    @mock.patch('cyborg.objects.Attribute.get_by_filter', autospec=True)
    def test_get_all_attributes_success(self, mock_list):
        mock_list.return_value = [self.fake_attr_obj]
        for context in self.read_all_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.get_json(ATTRIBUTE_URL, headers=headers)
            self.assertIsInstance(response['attributes'], list)

    def test_get_all_attributes_forbidden(self):
        for context in self.read_all_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(ATTRIBUTE_URL, headers=headers)

    @mock.patch('cyborg.objects.Attribute.get', autospec=True)
    def test_get_one_attribute_success(self, mock_get):
        mock_get.return_value = self.fake_attr_obj
        uuid = self.fake_attr_obj['uuid']
        for context in self.read_all_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.get_json(
                ATTRIBUTE_URL + '/%s' % uuid, headers=headers
            )
            self.assertEqual(uuid, response['uuid'])

    def test_get_one_attribute_forbidden(self):
        uuid = self.fake_attr_obj['uuid']
        for context in self.read_all_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(
                        ATTRIBUTE_URL + '/%s' % uuid, headers=headers
                    )

    @mock.patch('cyborg.objects.Attribute.create', autospec=True)
    def test_create_attribute_success(self, mock_create):
        mock_create.return_value = self.fake_attr_obj
        for context in self.admin_only_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.post_json(
                ATTRIBUTE_URL, self.fake_attr_dict, headers=headers
            )
            self.assertEqual(http.HTTPStatus.CREATED, response.status_int)

    def test_create_attribute_forbidden(self):
        for context in self.admin_only_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.post_json(
                        ATTRIBUTE_URL, self.fake_attr_dict, headers=headers
                    )

    @mock.patch('cyborg.objects.Attribute.destroy', autospec=True)
    @mock.patch('cyborg.objects.Attribute.get', autospec=True)
    def test_delete_attribute_success(self, mock_get, mock_destroy):
        mock_get.return_value = self.fake_attr_obj
        uuid = self.fake_attr_obj['uuid']
        for context in self.admin_only_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.delete(
                ATTRIBUTE_URL + '/%s' % uuid, headers=headers
            )
            self.assertEqual(http.HTTPStatus.NO_CONTENT, response.status_int)

    def test_delete_attribute_forbidden(self):
        uuid = self.fake_attr_obj['uuid']
        for context in self.admin_only_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.delete(ATTRIBUTE_URL + '/%s' % uuid, headers=headers)


class AttributePolicyNewDefaultsTest(base.BasePolicyTest):
    """Test attribute APIs with enforce_new_defaults=True.

    Verifies the new persona-based defaults for the 2026.2 SRBAC
    migration. Deprecated bridges are inactive so only the new
    check strings are evaluated.
    """

    def setUp(self):
        super().setUp()
        self.set_enforce_new_defaults(True)
        self.fake_attr_obj = fake_attribute.fake_attribute_obj(self.context)
        self.fake_attr_dict = fake_attribute.fake_db_attribute()

        # get_all and get_one: project_manager_or_admin. Policy checks
        # use the request context as target, so target carries the caller's
        # project_id. project_manager_api (role:manager and project_id
        # match) and admin_api (role:admin) both match.
        self.read_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
            self.project_manager_context,
        ]
        self.read_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.read_authorized_contexts)
        )

        # create/delete: admin_api — admin only.
        self.admin_only_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
        ]
        self.admin_only_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.admin_only_authorized_contexts)
        )

    @mock.patch('cyborg.objects.Attribute.get_by_filter', autospec=True)
    def test_get_all_attributes_new_defaults_success(self, mock_list):
        mock_list.return_value = [self.fake_attr_obj]
        for context in self.read_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(ATTRIBUTE_URL, headers=headers)
                self.assertIsInstance(response['attributes'], list)

    def test_get_all_attributes_new_defaults_forbidden(self):
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(ATTRIBUTE_URL, headers=headers)

    @mock.patch('cyborg.objects.Attribute.get', autospec=True)
    def test_get_one_attribute_new_defaults_success(self, mock_get):
        mock_get.return_value = self.fake_attr_obj
        uuid = self.fake_attr_obj['uuid']
        for context in self.read_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    ATTRIBUTE_URL + '/%s' % uuid, headers=headers
                )
                self.assertEqual(uuid, response['uuid'])

    def test_get_one_attribute_new_defaults_forbidden(self):
        uuid = self.fake_attr_obj['uuid']
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(
                        ATTRIBUTE_URL + '/%s' % uuid, headers=headers
                    )

    @mock.patch('cyborg.objects.Attribute.create', autospec=True)
    def test_create_attribute_new_defaults_success(self, mock_create):
        mock_create.return_value = self.fake_attr_obj
        for context in self.admin_only_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.post_json(
                    ATTRIBUTE_URL,
                    self.fake_attr_dict,
                    headers=headers,
                )
                self.assertEqual(http.HTTPStatus.CREATED, response.status_int)

    def test_create_attribute_new_defaults_forbidden(self):
        for context in self.admin_only_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.post_json(
                        ATTRIBUTE_URL,
                        self.fake_attr_dict,
                        headers=headers,
                    )

    @mock.patch('cyborg.objects.Attribute.destroy', autospec=True)
    @mock.patch('cyborg.objects.Attribute.get', autospec=True)
    def test_delete_attribute_new_defaults_success(
        self, mock_get, mock_destroy
    ):
        mock_get.return_value = self.fake_attr_obj
        uuid = self.fake_attr_obj['uuid']
        for context in self.admin_only_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.delete(
                    ATTRIBUTE_URL + '/%s' % uuid, headers=headers
                )
                self.assertEqual(
                    http.HTTPStatus.NO_CONTENT, response.status_int
                )

    def test_delete_attribute_new_defaults_forbidden(self):
        uuid = self.fake_attr_obj['uuid']
        for context in self.admin_only_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.delete(ATTRIBUTE_URL + '/%s' % uuid, headers=headers)
