# Copyright 2019 Intel, Inc.
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

from six.moves import http_client
import unittest
from unittest import mock

from oslo_serialization import jsonutils

from cyborg.api.controllers import base
from cyborg.api.controllers.v2 import arqs
from cyborg.common import exception
from cyborg.tests.unit.api.controllers.v2 import base as v2_test
from cyborg.tests.unit import fake_device_profile
from cyborg.tests.unit import fake_extarq


class TestARQsController(v2_test.APITestV2):

    ARQ_URL = '/accelerator_requests'

    def setUp(self):
        super(TestARQsController, self).setUp()
        self.headers = self.gen_headers(self.context)
        self.fake_extarqs = fake_extarq.get_fake_extarq_objs()
        self.fake_bind_extarqs = fake_extarq.get_fake_extarq_bind_objs()
        self.fake_resolved_extarqs = (
            fake_extarq.get_fake_extarq_resolved_objs())
        self.arqs_controller = arqs.ARQsController()

    def _validate_links(self, links, arq_uuid):
        has_self_link = False
        for link in links:
            if link['rel'] == 'self':
                has_self_link = True
                url = link['href']
                components = url.split('/')
                self.assertEqual(components[-1], arq_uuid)
        self.assertTrue(has_self_link)

    def _validate_arq(self, in_arq, out_arq):
        for field in in_arq.keys():
            if field != 'id':
                self.assertEqual(in_arq[field], out_arq[field])

        # Check that the link is properly set up
        self._validate_links(out_arq['links'], in_arq['uuid'])

    @mock.patch('cyborg.objects.ExtARQ.get')
    def test_get_one_by_uuid(self, mock_extarq):
        in_extarq = self.fake_extarqs[0]
        in_arq = in_extarq.arq
        mock_extarq.return_value = in_extarq
        uuid = in_arq['uuid']

        url = self.ARQ_URL + '/%s'
        out_arq = self.get_json(url % uuid, headers=self.headers)
        mock_extarq.assert_called_once()
        self._validate_arq(in_arq, out_arq)

    @mock.patch('cyborg.objects.ExtARQ.list')
    def test_get_all(self, mock_extarqs):
        # test get_all of any bind_state
        mock_extarqs.return_value = self.fake_extarqs
        data = self.get_json(self.ARQ_URL, headers=self.headers)
        out_arqs = data['arqs']

        result = isinstance(out_arqs, list)
        self.assertTrue(result)
        self.assertTrue(len(out_arqs), len(self.fake_extarqs))
        for in_extarq, out_arq in zip(self.fake_extarqs, out_arqs):
            self._validate_arq(in_extarq.arq, out_arq)

    @mock.patch('cyborg.objects.ExtARQ.list')
    def test_get_all_with_instance(self, mock_extarqs):
        # test get_all with instance
        mock_extarqs.return_value = self.fake_bind_extarqs
        instance_uuid = self.fake_bind_extarqs[0].arq.instance_uuid
        url = '%s?instance=%s' % (self.ARQ_URL, instance_uuid)
        data = self.get_json(url, headers=self.headers)
        out_arqs = data['arqs']

        result = isinstance(out_arqs, list)
        self.assertTrue(result)
        self.assertTrue(len(out_arqs), len(self.fake_bind_extarqs[:2]))
        for in_extarq, out_arq in zip(self.fake_bind_extarqs[:2], out_arqs):
            self._validate_arq(in_extarq.arq, out_arq)

    @mock.patch('cyborg.objects.ExtARQ.list')
    def test_get_all_with_bind_state(self, mock_extarqs):
        # test get_all with valid bind_state(resolved)
        mock_extarqs.return_value = self.fake_resolved_extarqs
        url = '%s?bind_state=resolved' % self.ARQ_URL
        data = self.get_json(url, headers=self.headers)
        out_arqs = data['arqs']

        result = isinstance(out_arqs, list)
        self.assertTrue(result)
        self.assertTrue(len(out_arqs), len(self.fake_resolved_extarqs[1:]))
        for in_extarq, out_arq in zip(self.fake_resolved_extarqs[1:],
                                      out_arqs):
            self._validate_arq(in_extarq.arq, out_arq)

    @mock.patch('cyborg.objects.ExtARQ.list')
    def test_get_all_with_instance_and_bind_state(self, mock_extarqs):
        # test get_all with instance and valid bind_state(resolved)
        mock_extarqs.return_value = self.fake_bind_extarqs[:3]
        instance_uuid = self.fake_bind_extarqs[0].arq.instance_uuid
        url = '%s?instance=%s&bind_state=resolved' % (
            self.ARQ_URL, instance_uuid)
        data = self.get_json(url, headers=self.headers)
        out_arqs = data['arqs']

        result = isinstance(out_arqs, list)
        self.assertTrue(result)
        self.assertTrue(len(out_arqs), len(self.fake_bind_extarqs[:2]))
        for in_extarq, out_arq in zip(self.fake_bind_extarqs[:2], out_arqs):
            self._validate_arq(in_extarq.arq, out_arq)

    @mock.patch('cyborg.objects.ExtARQ.list')
    def test_get_all_with_http_client_LOCKED(self, mock_extarqs):
        # test get_all if not all ARQs are in bound state
        mock_extarqs.return_value = self.fake_bind_extarqs
        instance_uuid = self.fake_bind_extarqs[0].arq.instance_uuid
        url = '%s?instance=%s&bind_state=resolved' % (
            self.ARQ_URL, instance_uuid)
        try:
            self.get_json(url, headers=self.headers)
        except Exception as e:
            exc = e
        self.assertIn('423 Locked', exc.args[0])

    @mock.patch('cyborg.objects.ExtARQ.list')
    def test_get_all_with_invalid_bind_state(self, mock_extarqs):
        # test get_all with bind_state=started
        mock_extarqs.return_value = self.fake_extarqs
        instance_uuid = self.fake_extarqs[0].arq.instance_uuid
        url = '%s?instance=%s&bind_state=started' % (
            self.ARQ_URL, instance_uuid)
        exc = None
        try:
            self.get_json(url, headers=self.headers)
        except Exception as e:
            exc = e
        # TODO(all) Cyborg does not have fake HTTPRequest Object now, so just
        # use assertIn here, improve this case with assertRaises later.
        self.assertIn(
            "Accelerator Requests cannot be requested with "
            "state started.", exc.args[0])

        url = '%s?bind_state=started' % (self.ARQ_URL)
        exc = None
        try:
            self.get_json(url, headers=self.headers)
        except Exception as e:
            exc = e
        # TODO(all) Cyborg does not have fake HTTPRequest Object now, so just
        # use assertIn here, improve this case with assertRaises later.
        self.assertIn(
            "Accelerator Requests cannot be requested with "
            "state started.", exc.args[0])

    @mock.patch('cyborg.objects.ExtARQ.list')
    def test_get_all_with_invalid_arq_state(self, mock_extarqs):
        # test get_all response "423 Locked"
        # set ARQ state to 'BindStarted'
        self.fake_extarqs[0].arq.state = 'BindStarted'
        mock_extarqs.return_value = self.fake_extarqs
        instance_uuid = self.fake_extarqs[0].arq.instance_uuid
        url = '%s?instance=%s&bind_state=resolved' % (
            self.ARQ_URL, instance_uuid)
        response = self.get_json(url, headers=self.headers, expect_errors=True)
        self.assertEqual(http_client.LOCKED, response.status_int)

    @mock.patch('cyborg.objects.DeviceProfile.get_by_name')
    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.arq_create')
    def test_create(self, mock_obj_extarq, mock_obj_dp):
        dp_list = fake_device_profile.get_obj_devprofs()
        mock_obj_dp.return_value = dp = dp_list[0]
        mock_obj_extarq.side_effect = self.fake_extarqs
        params = {'device_profile_name': dp['name']}
        response = self.post_json(self.ARQ_URL, params, headers=self.headers)
        data = jsonutils.loads(response.__dict__['controller_output'])
        out_arqs = data['arqs']

        self.assertEqual(http_client.CREATED, response.status_int)
        self.assertEqual(len(out_arqs), 3)
        for in_extarq, out_arq in zip(self.fake_extarqs, out_arqs):
            self._validate_arq(in_extarq.arq, out_arq)
        for idx, out_arq in enumerate(out_arqs):
            dp_group_id = idx
            self.assertEqual(dp_group_id, out_arq['device_profile_group_id'])

    @mock.patch('cyborg.objects.DeviceProfile.get_by_name')
    @mock.patch('cyborg.objects.ExtARQ.create')
    def test_create_with_wrong_dp(self, mock_obj_extarq, mock_obj_dp):
        mock_obj_dp.side_effect = Exception
        mock_obj_extarq.side_effect = self.fake_extarqs
        params = {'device_profile_name': 'wrong_device_profile_name'}
        exc = None
        try:
            self.post_json(self.ARQ_URL, params, headers=self.headers)
        except Exception as e:
            exc = e
        self.assertIn(
            "Device Profile not found with "
            "name=wrong_device_profile_name", exc.args[0])

    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.arq_delete_by_uuid')
    @mock.patch('cyborg.conductor.rpcapi.ConductorAPI.'
                'arq_delete_by_instance_uuid')
    def test_delete(self, mock_by_inst, mock_by_arq):
        url = self.ARQ_URL
        arq = self.fake_extarqs[0].arq
        instance = arq.instance_uuid

        mock_by_arq.return_value = None
        args = '?' + "arqs=" + str(arq['uuid'])
        response = self.delete(url + args, headers=self.headers)
        self.assertEqual(http_client.NO_CONTENT, response.status_int)

        mock_by_inst.return_value = None
        args = '?' + "instance=" + instance
        response = self.delete(url + args, headers=self.headers)
        self.assertEqual(http_client.NO_CONTENT, response.status_int)

    @unittest.skip("Need more code to implement _get_resource in rbac")
    def test_delete_with_non_default(self):
        value = {"is_admin": False, "roles": "user", "is_admin_project": False}
        ct = self.gen_context(value)
        headers = self.gen_headers(ct)
        url = self.ARQ_URL
        arq = self.fake_extarqs[0].arq
        args = '?' + "arqs=" + str(arq['uuid'])
        exc = None
        try:
            self.delete(url + args, headers=headers)
        except Exception as e:
            exc = e
        # Cyborg does not raise different exception when policy check failed
        # now, improve this case with assertRaises later.
        self.assertIn("Bad response: 403 Forbidden", exc.args[0])

    @mock.patch.object(arqs.ARQsController, '_check_if_already_bound')
    @mock.patch('cyborg.objects.ExtARQ.apply_patch')
    def test_apply_patch(self, mock_apply_patch, mock_check_if_bound):
        """Test the happy path."""
        patch_list, device_rp_uuid = fake_extarq.get_patch_list()
        arq_uuids = list(patch_list.keys())
        obj_extarq = self.fake_extarqs[0]
        valid_fields = {
            arq_uuid: {
                'hostname': obj_extarq.arq.hostname,
                'device_rp_uuid': device_rp_uuid,
                'instance_uuid': obj_extarq.arq.instance_uuid}
            for arq_uuid in arq_uuids}

        self.patch_json(self.ARQ_URL, params=patch_list,
                        headers=self.headers)

        mock_apply_patch.assert_called_once_with(mock.ANY, patch_list,
                                                 valid_fields)
        mock_check_if_bound.assert_called_once_with(mock.ANY, valid_fields)

    @mock.patch.object(arqs.ARQsController, '_check_if_already_bound')
    @mock.patch('cyborg.objects.ExtARQ.apply_patch')
    def test_apply_patch_allow_project_id(
            self, mock_apply_patch, mock_check_if_bound):
        patch_list, _ = fake_extarq.get_patch_list()
        for arq_uuid, patch in patch_list.items():
            patch.append({'path': '/project_id', 'op': 'add',
                          'value': 'b1c76756ac2e482789a8e1c5f4bf065e'})
        arq_uuids = list(patch_list.keys())
        valid_fields = {
            arq_uuid: {
                'hostname': 'myhost',
                'device_rp_uuid': 'fb16c293-5739-4c84-8590-926f9ab16669',
                'instance_uuid': '5922a70f-1e06-4cfd-88dd-a332120d7144',
                'project_id': 'b1c76756ac2e482789a8e1c5f4bf065e'}
            for arq_uuid in arq_uuids}

        self.patch_json(self.ARQ_URL, params=patch_list,
                        headers={base.Version.current_api_version:
                                 'accelerator 2.1'})
        mock_apply_patch.assert_called_once_with(mock.ANY, patch_list,
                                                 valid_fields)
        mock_check_if_bound.assert_called_once_with(mock.ANY, valid_fields)

    def test_apply_patch_not_allow_project_id(self):
        patch_list, _ = fake_extarq.get_patch_list()
        for arq_uuid, patch in patch_list.items():
            patch.append({'path': '/project_id', 'op': 'add',
                          'value': 'b1c76756ac2e482789a8e1c5f4bf065e'})
        response = self.patch_json(self.ARQ_URL, params=patch_list,
                                   headers=self.headers,
                                   expect_errors=True)
        self.assertEqual(http_client.NOT_ACCEPTABLE, response.status_code)
        self.assertTrue(response.json['error_message'])

    # TODO(all): Add exception test cases for apply_patch.

    @mock.patch('cyborg.objects.ExtARQ.list')
    def test_check_if_bound(self, mock_extarq_list):
        """Test the happy path."""
        extarqs = fake_extarq.get_fake_extarq_objs()
        mock_extarq_list.return_value = extarqs

        # Not the instance UUID in extarqs above
        instance_uuid = 'ffbb66f6-99f6-4a85-a90c-fd8e8fb35f16'
        valid_fields = {
            extarq.arq['uuid']: {
                'hostname': 'myhost',
                'device_rp_uuid': 'fb16c293-5739-4c84-8590-926f9ab16669',
                'instance_uuid': instance_uuid}
            for extarq in extarqs}

        self.arqs_controller._check_if_already_bound(
            self.context, valid_fields)
        mock_extarq_list.assert_called_once_with(self.context)

    @mock.patch('cyborg.objects.ExtARQ.list')
    def test_check_if_bound_exception(self, mock_extarq_list):
        """Test that an exception is raised if binding request specifies
           an instance that already has ARQs.
        """
        extarqs = fake_extarq.get_fake_extarq_objs()
        mock_extarq_list.return_value = extarqs

        # Same instance UUID as in extarqs above, thus triggering exception
        instance_uuid = extarqs[0].arq['instance_uuid']
        valid_fields = {
            extarq.arq['uuid']: {
                'hostname': 'myhost',
                'device_rp_uuid': 'fb16c293-5739-4c84-8590-926f9ab16669',
                'instance_uuid': instance_uuid}
            for extarq in extarqs}

        expected_err = ('Instance %s already has accelerator requests. '
                        'Cannot bind additional ARQs.') % instance_uuid

        self.assertRaisesRegex(
            exception.PatchError, expected_err,
            self.arqs_controller._check_if_already_bound,
            self.context, valid_fields)
