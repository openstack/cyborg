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
from cyborg.tests.unit import fake_deployable
from cyborg.tests.unit import fake_device
from cyborg.tests.unit.policies import base


DEVICE_URL = '/devices'


def _stub_device_update_dependencies(
    context, fake_dev, mock_dep_get, mock_attr_filter
):
    mock_dep_get.return_value = fake_deployable.fake_deployable_obj(
        context,
        id=fake_dev.id,
        rp_uuid='00000000-0000-0000-0000-000000000001',
        num_accelerators=4,
    )
    mock_attr_filter.return_value = [
        fake_attribute.fake_attribute_obj(context, value='CUSTOM_FOO')
    ]


class DevicePolicyTest(base.BasePolicyTest):
    """Test device APIs policies with all possible contexts.

    This class defines the set of contexts with different roles
    which are allowed and not allowed to pass the policy checks.
    With those set of contexts, it will call the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super().setUp()
        self.fake_devices = fake_device.get_fake_devices_objs()

        # New default: project_manager_or_admin.
        # Deprecated bridge on the DocumentedRuleDefault: rule:admin_api.
        # With enforce_new_defaults=False, oslo.policy builds an OrCheck
        # at two levels:
        #
        # 1. The DocumentedRuleDefault for get_all/get_one ORs its new
        #    check_str (rule:project_manager_or_admin) with its deprecated
        #    bridge (rule:admin_api).
        # 2. The project_manager_or_admin RuleDefault itself has
        #    deprecated_rule=DEPRECATED_ADMIN_OR_OWNER, so oslo.policy
        #    also ORs that rule's check with its own deprecated bridge
        #    (is_admin:True or project_id:%(project_id)s).
        #
        # Policy checks use the request context as target, so the target
        # project_id equals the caller's project_id. The deprecated bridge
        # on project_manager_or_admin therefore matches any project-scoped
        # context. Only system-scoped contexts are rejected by
        # enforce_scope=True.
        self.read_authorized_contexts = [
            self.legacy_admin_context,
            self.legacy_owner_context,
            self.project_admin_context,
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

        # disable and enable remain admin-only (same new default and
        # deprecated bridge: rule:admin_api). The request-context target is
        # irrelevant because admin_api has no project_id requirement.
        self.write_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
        ]
        self.write_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.write_authorized_contexts)
        )

    @mock.patch('cyborg.objects.Device.list', autospec=True)
    def test_get_all_devices_success(self, mock_list):
        mock_list.return_value = self.fake_devices
        for context in self.read_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.get_json(
                DEVICE_URL, headers=headers, return_json=False
            )
            self.assertEqual(http.HTTPStatus.OK, response.status_int)
            self.assertEqual(
                len(self.fake_devices), len(response.json['devices'])
            )

    def test_get_all_devices_forbidden(self):
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(DEVICE_URL, headers=headers)

    @mock.patch('cyborg.objects.Device.list', autospec=True)
    def test_get_all_devices_system_scope_forbidden(self, mock_list):
        headers = self.gen_headers(self.system_admin_context)
        with self.assertRaisesRegex(Exception, base.POLICY_DENY_EXPECTED):
            self.get_json(DEVICE_URL, headers=headers)
        mock_list.assert_not_called()

    @mock.patch('cyborg.objects.Device.get', autospec=True)
    def test_get_one_device_success(self, mock_get):
        fake_dev = self.fake_devices[0]
        mock_get.return_value = fake_dev
        uuid = fake_dev['uuid']
        for context in self.read_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.get_json(
                DEVICE_URL + '/%s' % uuid, headers=headers
            )
            self.assertEqual(uuid, response['uuid'])

    def test_get_one_device_forbidden(self):
        uuid = self.fake_devices[0]['uuid']
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(DEVICE_URL + '/%s' % uuid, headers=headers)

    @mock.patch(
        'cyborg.api.controllers.v2.devices.placement_client.PlacementClient',
        autospec=True,
    )
    @mock.patch('cyborg.objects.Attribute.get_by_filter', autospec=True)
    @mock.patch('cyborg.objects.Deployable.get_by_id', autospec=True)
    @mock.patch('cyborg.objects.Device.save', autospec=True)
    @mock.patch('cyborg.objects.Device.get', autospec=True)
    def test_disable_device_success(
        self,
        mock_get,
        mock_save,
        mock_dep_get,
        mock_attr_filter,
        mock_pc_cls,
    ):
        fake_dev = self.fake_devices[0]
        mock_get.return_value = fake_dev
        _stub_device_update_dependencies(
            self.context, fake_dev, mock_dep_get, mock_attr_filter
        )
        for context in self.write_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.post_json(
                DEVICE_URL + '/%s/disable' % fake_dev.uuid,
                {},
                headers=headers,
            )
            self.assertEqual(http.HTTPStatus.NO_CONTENT, response.status_int)

    def test_disable_device_forbidden(self):
        uuid = self.fake_devices[0]['uuid']
        for context in self.write_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.post_json(
                        DEVICE_URL + '/%s/disable' % uuid,
                        {},
                        headers=headers,
                    )

    @mock.patch('cyborg.objects.Device.get', autospec=True)
    def test_disable_device_system_scope_forbidden(self, mock_get):
        uuid = self.fake_devices[0]['uuid']
        headers = self.gen_headers(self.system_admin_context)
        with self.assertRaisesRegex(Exception, base.POLICY_DENY_EXPECTED):
            self.post_json(
                DEVICE_URL + '/%s/disable' % uuid,
                {},
                headers=headers,
            )
        mock_get.assert_not_called()

    @mock.patch(
        'cyborg.api.controllers.v2.devices.placement_client.PlacementClient',
        autospec=True,
    )
    @mock.patch('cyborg.objects.Attribute.get_by_filter', autospec=True)
    @mock.patch('cyborg.objects.Deployable.get_by_id', autospec=True)
    @mock.patch('cyborg.objects.Device.save', autospec=True)
    @mock.patch('cyborg.objects.Device.get', autospec=True)
    def test_enable_device_success(
        self,
        mock_get,
        mock_save,
        mock_dep_get,
        mock_attr_filter,
        mock_pc_cls,
    ):
        fake_dev = self.fake_devices[0]
        mock_get.return_value = fake_dev
        _stub_device_update_dependencies(
            self.context, fake_dev, mock_dep_get, mock_attr_filter
        )
        for context in self.write_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.post_json(
                DEVICE_URL + '/%s/enable' % fake_dev.uuid,
                {},
                headers=headers,
            )
            self.assertEqual(http.HTTPStatus.NO_CONTENT, response.status_int)

    def test_enable_device_forbidden(self):
        uuid = self.fake_devices[0]['uuid']
        for context in self.write_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.post_json(
                        DEVICE_URL + '/%s/enable' % uuid,
                        {},
                        headers=headers,
                    )


class DevicePolicyNewDefaultsTest(base.BasePolicyTest):
    """Test device API policies with enforce_new_defaults=True.

    Verifies that the new persona-based check strings are evaluated
    correctly when the operator opts in to new defaults.
    """

    def setUp(self):
        super().setUp()
        # Switch to new defaults and re-initialise the enforcer so that
        # the DocumentedRuleDefault check strings are evaluated without
        # the deprecated bridge ORed in.
        self.set_enforce_new_defaults(True)
        self.fake_devices = fake_device.get_fake_devices_objs()

        # get_all and get_one use the request context as target, so the
        # target carries the caller's project_id. New default:
        # project_manager_or_admin (role:manager and project_id match,
        # or role:admin).
        self.read_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
            self.project_manager_context,
        ]
        self.read_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.read_authorized_contexts)
        )

        # device:disable and device:enable: admin_api (role:admin) in both
        # new default and deprecated bridge, so admin-only in both modes.
        self.write_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
        ]
        self.write_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.write_authorized_contexts)
        )

    @mock.patch('cyborg.objects.Device.list', autospec=True)
    def test_get_all_devices_new_defaults_success(self, mock_list):
        mock_list.return_value = self.fake_devices
        for context in self.read_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    DEVICE_URL, headers=headers, return_json=False
                )
                self.assertEqual(http.HTTPStatus.OK, response.status_int)
                self.assertEqual(
                    len(self.fake_devices),
                    len(response.json['devices']),
                )

    def test_get_all_devices_new_defaults_forbidden(self):
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(DEVICE_URL, headers=headers)

    @mock.patch('cyborg.objects.Device.list', autospec=True)
    def test_get_all_devices_new_defaults_system_scope_forbidden(
        self, mock_list
    ):
        headers = self.gen_headers(self.system_admin_context)
        with self.assertRaisesRegex(Exception, base.POLICY_DENY_EXPECTED):
            self.get_json(DEVICE_URL, headers=headers)
        mock_list.assert_not_called()

    @mock.patch('cyborg.objects.Device.get', autospec=True)
    def test_get_one_device_new_defaults_success(self, mock_get):
        fake_dev = self.fake_devices[0]
        mock_get.return_value = fake_dev
        uuid = fake_dev['uuid']
        for context in self.read_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.get_json(
                    DEVICE_URL + '/%s' % uuid, headers=headers
                )
                self.assertEqual(uuid, response['uuid'])

    def test_get_one_device_new_defaults_forbidden(self):
        uuid = self.fake_devices[0]['uuid']
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(DEVICE_URL + '/%s' % uuid, headers=headers)

    @mock.patch(
        'cyborg.api.controllers.v2.devices.placement_client.PlacementClient',
        autospec=True,
    )
    @mock.patch('cyborg.objects.Attribute.get_by_filter', autospec=True)
    @mock.patch('cyborg.objects.Deployable.get_by_id', autospec=True)
    @mock.patch('cyborg.objects.Device.save', autospec=True)
    @mock.patch('cyborg.objects.Device.get', autospec=True)
    def test_disable_device_new_defaults_success(
        self,
        mock_get,
        mock_save,
        mock_dep_get,
        mock_attr_filter,
        mock_pc_cls,
    ):
        fake_dev = self.fake_devices[0]
        mock_get.return_value = fake_dev
        _stub_device_update_dependencies(
            self.context, fake_dev, mock_dep_get, mock_attr_filter
        )
        for context in self.write_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.post_json(
                    DEVICE_URL + '/%s/disable' % fake_dev.uuid,
                    {},
                    headers=headers,
                )
                self.assertEqual(
                    http.HTTPStatus.NO_CONTENT, response.status_int
                )

    def test_disable_device_new_defaults_forbidden(self):
        uuid = self.fake_devices[0]['uuid']
        for context in self.write_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.post_json(
                        DEVICE_URL + '/%s/disable' % uuid,
                        {},
                        headers=headers,
                    )

    @mock.patch('cyborg.objects.Device.get', autospec=True)
    def test_disable_device_new_defaults_system_scope_forbidden(
        self, mock_get
    ):
        uuid = self.fake_devices[0]['uuid']
        headers = self.gen_headers(self.system_admin_context)
        with self.assertRaisesRegex(Exception, base.POLICY_DENY_EXPECTED):
            self.post_json(
                DEVICE_URL + '/%s/disable' % uuid,
                {},
                headers=headers,
            )
        mock_get.assert_not_called()

    @mock.patch(
        'cyborg.api.controllers.v2.devices.placement_client.PlacementClient',
        autospec=True,
    )
    @mock.patch('cyborg.objects.Attribute.get_by_filter', autospec=True)
    @mock.patch('cyborg.objects.Deployable.get_by_id', autospec=True)
    @mock.patch('cyborg.objects.Device.save', autospec=True)
    @mock.patch('cyborg.objects.Device.get', autospec=True)
    def test_enable_device_new_defaults_success(
        self,
        mock_get,
        mock_save,
        mock_dep_get,
        mock_attr_filter,
        mock_pc_cls,
    ):
        fake_dev = self.fake_devices[0]
        mock_get.return_value = fake_dev
        _stub_device_update_dependencies(
            self.context, fake_dev, mock_dep_get, mock_attr_filter
        )
        for context in self.write_authorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                response = self.post_json(
                    DEVICE_URL + '/%s/enable' % fake_dev.uuid,
                    {},
                    headers=headers,
                )
                self.assertEqual(
                    http.HTTPStatus.NO_CONTENT, response.status_int
                )

    def test_enable_device_new_defaults_forbidden(self):
        uuid = self.fake_devices[0]['uuid']
        for context in self.write_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.post_json(
                        DEVICE_URL + '/%s/enable' % uuid,
                        {},
                        headers=headers,
                    )
