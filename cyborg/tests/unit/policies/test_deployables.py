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

from oslo_serialization import jsonutils

from cyborg.tests.unit import fake_deployable
from cyborg.tests.unit import fake_device
from cyborg.tests.unit.policies import base


DEPLOYABLE_URL = '/deployables'


class DeployablePolicyTest(base.BasePolicyTest):
    """Test deployable APIs policies with all possible contexts.

    This class defines the set of contexts with different roles
    which are allowed and not allowed to pass the policy checks.
    With those set of contexts, it will call the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super().setUp()
        self.fake_dep = fake_deployable.fake_deployable_obj(self.context)
        self.fake_dev = fake_device.get_fake_devices_objs()[0]
        bdf = {
            'domain': '0000',
            'bus': '00',
            'device': '01',
            'function': '1',
        }
        self.cpid = {
            'id': 0,
            'uuid': 'e4a66b0d-b377-40d6-9cdc-6bf7e720e596',
            'device_id': '1',
            'cpid_type': 'PCI',
            'cpid_info': jsonutils.dumps(bdf).encode('utf-8'),
        }
        self.image_uuid = '9a17439a-85d0-4c53-a3d3-0f68a2eac896'

        # New default for reads: project_manager_or_admin.
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
        # project_id equals the caller's project_id. The base rule's
        # deprecated bridge therefore matches any project-scoped context.
        # Only system-scoped contexts are rejected by enforce_scope=True.
        # The legacy and new checks for program are both admin_api, so it
        # is admin-only in both modes.
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
        self.program_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
        ]
        self.program_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.program_authorized_contexts)
        )

    @mock.patch('cyborg.objects.Deployable.list', autospec=True)
    def test_get_all_deployables_success(self, mock_list):
        mock_list.return_value = [self.fake_dep]
        for context in self.read_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.get_json(DEPLOYABLE_URL, headers=headers)
            self.assertIsInstance(response['deployables'], list)

    def test_get_all_deployables_forbidden(self):
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(DEPLOYABLE_URL, headers=headers)

    @mock.patch('cyborg.objects.Attribute.get_by_filter', autospec=True)
    @mock.patch('cyborg.objects.Deployable.get', autospec=True)
    def test_get_one_deployable_success(self, mock_get, mock_attr):
        mock_get.return_value = self.fake_dep
        mock_attr.return_value = []
        uuid = self.fake_dep['uuid']
        for context in self.read_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.get_json(
                DEPLOYABLE_URL + '/%s' % uuid, headers=headers
            )
            self.assertEqual(uuid, response['uuid'])

    def test_get_one_deployable_forbidden(self):
        uuid = self.fake_dep['uuid']
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(
                        DEPLOYABLE_URL + '/%s' % uuid, headers=headers
                    )

    @mock.patch('cyborg.objects.Device.get_by_device_id', autospec=True)
    @mock.patch('cyborg.objects.Deployable.get_cpid_list', autospec=True)
    @mock.patch('cyborg.objects.Deployable.get', autospec=True)
    @mock.patch('cyborg.agent.rpcapi.AgentAPI.fpga_program', autospec=True)
    def test_program_deployable_success(
        self,
        mock_program,
        mock_dep_get,
        mock_cpid,
        mock_dev_get,
    ):
        dep_uuid = self.fake_dep['uuid']
        mock_dep_get.return_value = self.fake_dep
        mock_dev_get.return_value = self.fake_dev
        # Use side_effect so a fresh dict copy is returned on every call;
        # the controller mutates cpid_list[0]['cpid_info'] in-place and a
        # shared return_value would be corrupted on the second iteration.
        mock_cpid.side_effect = lambda *args: [dict(self.cpid)]
        mock_program.return_value = True
        body = [{'image_uuid': self.image_uuid}]
        for context in self.program_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.patch_json(
                DEPLOYABLE_URL + '/%s/program' % dep_uuid,
                [{'path': '/bitstream_id', 'value': body, 'op': 'replace'}],
                headers=headers,
            )
            self.assertEqual(http.HTTPStatus.OK, response.status_code)

    def test_program_deployable_forbidden(self):
        dep_uuid = self.fake_dep['uuid']
        body = [{'image_uuid': self.image_uuid}]
        for context in self.program_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.patch_json(
                        DEPLOYABLE_URL + '/%s/program' % dep_uuid,
                        [
                            {
                                'path': '/bitstream_id',
                                'value': body,
                                'op': 'replace',
                            }
                        ],
                        headers=headers,
                    )


class DeployablePolicyNewDefaultsTest(base.BasePolicyTest):
    """Test deployable API policies with enforce_new_defaults=True.

    Verifies that the new DocumentedRuleDefault check strings take
    effect when enforce_new_defaults is enabled, without relying on
    deprecated-rule bridges.
    """

    def setUp(self):
        super().setUp()
        self.set_enforce_new_defaults(True)
        self.fake_dep = fake_deployable.fake_deployable_obj(self.context)
        self.fake_dev = fake_device.get_fake_devices_objs()[0]
        bdf = {
            'domain': '0000',
            'bus': '00',
            'device': '01',
            'function': '1',
        }
        self.cpid = {
            'id': 0,
            'uuid': 'e4a66b0d-b377-40d6-9cdc-6bf7e720e596',
            'device_id': '1',
            'cpid_type': 'PCI',
            'cpid_info': jsonutils.dumps(bdf).encode('utf-8'),
        }
        self.image_uuid = '9a17439a-85d0-4c53-a3d3-0f68a2eac896'

        # New default for reads: project_manager_or_admin.
        # With enforce_new_defaults=True the deprecated bridge is
        # suppressed. Policy checks use the request context as target,
        # so the target carries the caller's project_id. Managers pass
        # via role:manager and project_id match.
        self.read_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
            self.project_manager_context,
        ]
        self.read_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.read_authorized_contexts)
        )
        # program: admin_api in both old and new default.
        self.program_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
        ]
        self.program_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.program_authorized_contexts)
        )

    @mock.patch('cyborg.objects.Deployable.list', autospec=True)
    def test_get_all_deployables_new_defaults_success(self, mock_list):
        mock_list.return_value = [self.fake_dep]
        for context in self.read_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.get_json(DEPLOYABLE_URL, headers=headers)
            self.assertIsInstance(response['deployables'], list)

    def test_get_all_deployables_new_defaults_forbidden(self):
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(DEPLOYABLE_URL, headers=headers)

    @mock.patch('cyborg.objects.Attribute.get_by_filter', autospec=True)
    @mock.patch('cyborg.objects.Deployable.get', autospec=True)
    def test_get_one_deployable_new_defaults_success(
        self, mock_get, mock_attr
    ):
        mock_get.return_value = self.fake_dep
        mock_attr.return_value = []
        uuid = self.fake_dep['uuid']
        for context in self.read_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.get_json(
                DEPLOYABLE_URL + '/%s' % uuid, headers=headers
            )
            self.assertEqual(uuid, response['uuid'])

    def test_get_one_deployable_new_defaults_forbidden(self):
        uuid = self.fake_dep['uuid']
        for context in self.read_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.get_json(
                        DEPLOYABLE_URL + '/%s' % uuid,
                        headers=headers,
                    )

    @mock.patch('cyborg.objects.Device.get_by_device_id', autospec=True)
    @mock.patch('cyborg.objects.Deployable.get_cpid_list', autospec=True)
    @mock.patch('cyborg.objects.Deployable.get', autospec=True)
    @mock.patch('cyborg.agent.rpcapi.AgentAPI.fpga_program', autospec=True)
    def test_program_deployable_new_defaults_success(
        self,
        mock_program,
        mock_dep_get,
        mock_cpid,
        mock_dev_get,
    ):
        dep_uuid = self.fake_dep['uuid']
        mock_dep_get.return_value = self.fake_dep
        mock_dev_get.return_value = self.fake_dev
        mock_cpid.side_effect = lambda *args: [dict(self.cpid)]
        mock_program.return_value = True
        body = [{'image_uuid': self.image_uuid}]
        for context in self.program_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.patch_json(
                DEPLOYABLE_URL + '/%s/program' % dep_uuid,
                [
                    {
                        'path': '/bitstream_id',
                        'value': body,
                        'op': 'replace',
                    }
                ],
                headers=headers,
            )
            self.assertEqual(http.HTTPStatus.OK, response.status_code)

    def test_program_deployable_new_defaults_forbidden(self):
        dep_uuid = self.fake_dep['uuid']
        body = [{'image_uuid': self.image_uuid}]
        for context in self.program_unauthorized_contexts:
            with self.subTest(context=context):
                headers = self.gen_headers(context)
                with self.assertRaisesRegex(
                    Exception, base.POLICY_DENY_EXPECTED
                ):
                    self.patch_json(
                        DEPLOYABLE_URL + '/%s/program' % dep_uuid,
                        [
                            {
                                'path': '/bitstream_id',
                                'value': body,
                                'op': 'replace',
                            }
                        ],
                        headers=headers,
                    )
