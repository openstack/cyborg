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

from cyborg.tests.unit import fake_device
from cyborg.tests.unit.policies import base


DEVICE_URL = '/devices'


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

        # rule:admin_api with project scope enforced.
        self.read_authorized_contexts = [
            self.legacy_admin_context,
            self.project_admin_context,
        ]
        self.read_unauthorized_contexts = list(
            set(self.all_contexts) - set(self.read_authorized_contexts)
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
        'cyborg.api.controllers.v2.devices.placement_client.PlacementClient'
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
        mock_dep = mock.MagicMock()
        mock_dep.id = fake_dev.id
        mock_dep.rp_uuid = '00000000-0000-0000-0000-000000000001'
        mock_dep.num_accelerators = 4
        mock_dep_get.return_value = mock_dep
        mock_attr_filter.return_value = [mock.MagicMock(value='CUSTOM_FOO')]
        mock_pc_cls.return_value = mock.MagicMock()
        for context in self.read_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.post_json(
                DEVICE_URL + '/%s/disable' % fake_dev.uuid,
                {},
                headers=headers,
            )
            self.assertEqual(http.HTTPStatus.NO_CONTENT, response.status_int)

    def test_disable_device_forbidden(self):
        uuid = self.fake_devices[0]['uuid']
        for context in self.read_unauthorized_contexts:
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

    @mock.patch(
        'cyborg.api.controllers.v2.devices.placement_client.PlacementClient'
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
        mock_dep = mock.MagicMock()
        mock_dep.id = fake_dev.id
        mock_dep.rp_uuid = '00000000-0000-0000-0000-000000000001'
        mock_dep.num_accelerators = 4
        mock_dep_get.return_value = mock_dep
        mock_attr_filter.return_value = [mock.MagicMock(value='CUSTOM_FOO')]
        mock_pc_cls.return_value = mock.MagicMock()
        for context in self.read_authorized_contexts:
            headers = self.gen_headers(context)
            response = self.post_json(
                DEVICE_URL + '/%s/enable' % fake_dev.uuid,
                {},
                headers=headers,
            )
            self.assertEqual(http.HTTPStatus.NO_CONTENT, response.status_int)

    def test_enable_device_forbidden(self):
        uuid = self.fake_devices[0]['uuid']
        for context in self.read_unauthorized_contexts:
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
