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
from oslo_serialization import jsonutils
from six.moves import http_client
from unittest import mock

from cyborg.api.controllers.v2 import device_profiles

from cyborg.tests.unit import fake_device_profile
from cyborg.tests.unit.policies import base


LOG = logging.getLogger(__name__)
DP_URL = '/device_profiles'


class DeviceProfilePolicyTest(base.BasePolicyTest):
    """Test device_profile APIs policies with all possible contexts.

    This class defines the set of context with different roles
    which are allowed and not allowed to pass the policy checks.
    With those set of context, it will call the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super(DeviceProfilePolicyTest, self).setUp()

        self.flags(enforce_scope=False, group="oslo_policy")
        self.controller = device_profiles.DeviceProfilesController()
        self.fake_dp_objs = fake_device_profile.get_obj_devprofs()
        self.fake_dps = fake_device_profile.get_api_devprofs()
        # check both legacy and new policies for create APIs
        self.create_authorized_contexts = [
            self.legacy_admin_context,  # legacy: admin
            self.system_admin_context,  # new policy: system_admin
            self.project_admin_context
        ]
        self.create_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.create_authorized_contexts))

        # check both legacy and new policies for delete APIs
        self.delete_authorized_contexts = [
            # legacy: admin_or_owner
            self.legacy_admin_context,
            # NOTE(yumeng) although the legacy rule is admin_or_owner,
            # cyborg does not "actually" support owner check for
            # device profile, so we just uncomment legacy_owner_context here.
            # If later we need support owner policy, we should recheck here.
            # self.legacy_owner_context,
            self.system_admin_context,  # new policy: system_admin
            self.project_admin_context
        ]
        self.delete_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.delete_authorized_contexts))

    def _validate_links(self, links, dp_uuid):
        has_self_link = False
        for link in links:
            if link['rel'] == 'self':
                has_self_link = True
                url = link['href']
                components = url.split('/')
                self.assertEqual(components[-1], dp_uuid)
        self.assertTrue(has_self_link)

    def _validate_dp(self, in_dp, out_dp):
        self.assertEqual(in_dp['name'], out_dp['name'])
        self.assertEqual(in_dp['uuid'], out_dp['uuid'])
        self.assertEqual(in_dp['groups'], out_dp['groups'])

        # Check that the link is properly set up
        self._validate_links(out_dp['links'], in_dp['uuid'])

    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.device_profile_create')
    def test_create_device_profile_success(self, mock_cond_dp):
        mock_cond_dp.return_value = self.fake_dp_objs[0]
        dp = [self.fake_dps[0]]
        dp[0]['created_at'] = str(dp[0]['created_at'])

        for context in self.create_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.post_json(DP_URL, dp, headers=headers)
            out_dp = jsonutils.loads(response.controller_output)

            self.assertEqual(http_client.CREATED, response.status_int)
            self._validate_dp(dp[0], out_dp)

    def test_create_device_profile_forbidden(self):
        dp = [self.fake_dps[0]]
        dp[0]['created_at'] = str(dp[0]['created_at'])
        for context in self.create_unauthorized_contexts:
            headers = self.gen_headers(context)
            try:
                self.post_json(DP_URL, dp, headers=headers)
            except Exception as e:
                exc = e
            self.assertIn("Bad response: 403 Forbidden", exc.args[0])

    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.device_profile_delete')
    @mock.patch('cyborg.objects.DeviceProfile.get_by_name')
    @mock.patch('cyborg.objects.DeviceProfile.get_by_uuid')
    def test_delete_device_profile_success(self, mock_dp_uuid,
                                           mock_dp_name, mock_cond_del):
        for context in self.delete_authorized_contexts:
            headers = self.gen_headers(context)
            # Delete by UUID
            url = DP_URL + "/5d2c0797-c3cd-4f4b-b0d0-2cc5e99ef66e"
            response = self.delete(url, headers=headers)
            self.assertEqual(http_client.NO_CONTENT, response.status_int)
            # Delete by name
            url = DP_URL + "/mydp"
            response = self.delete(url, headers=headers)
            self.assertEqual(http_client.NO_CONTENT, response.status_int)

    def test_delete_device_profile_forbidden(self):
        dp = self.fake_dp_objs[0]
        url = DP_URL + '/%s'
        exc = None
        for context in self.delete_unauthorized_contexts:
            headers = self.gen_headers(context)
            try:
                self.delete(url % dp['uuid'], headers=headers)
            except Exception as e:
                exc = e
            self.assertIn("Bad response: 403 Forbidden", exc.args[0])


class DeviceProfileScopeTypePolicyTest(DeviceProfilePolicyTest):
    """Test device_profile APIs policies with system scope enabled.
    This class set the cyborg.conf [oslo_policy] enforce_scope to True
    so that we can switch on the scope checking on oslo policy side.
    It defines the set of context with scoped token
    which are allowed and not allowed to pass the policy checks.
    With those set of context, it will run the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super(DeviceProfileScopeTypePolicyTest, self).setUp()
        self.flags(enforce_scope=True, group="oslo_policy")

        # check that system_admin is able to do create and delete operations.
        self.create_authorized_contexts = [
            self.system_admin_context]
        self.delete_authorized_contexts = self.create_authorized_contexts
        # Check that non-system or non-admin is not able to perform the system
        # level actions on device_profiles.
        self.create_unauthorized_contexts = [
            self.legacy_admin_context, self.system_member_context,
            self.system_reader_context, self.system_foo_context,
            self.project_admin_context, self.project_member_context,
            self.other_project_member_context,
            self.project_foo_context, self.project_reader_context
        ]
        self.delete_unauthorized_contexts = self.create_unauthorized_contexts
