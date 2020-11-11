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

from http import HTTPStatus
from oslo_serialization import jsonutils
from unittest import mock

from cyborg.common import exception
from cyborg.tests.unit.api.controllers.v2 import base as v2_test
from cyborg.tests.unit import fake_deployable
from cyborg.tests.unit import fake_device


class TestFPGAProgramController(v2_test.APITestV2):

    def setUp(self):
        super(TestFPGAProgramController, self).setUp()
        self.headers = self.gen_headers(self.context)
        self.deployable_uuids = ['0acbf8d6-e02a-4394-aae3-57557d209498']
        self.existent_image_uuid = "9a17439a-85d0-4c53-a3d3-0f68a2eac896"
        self.nonexistent_image_uuid = "1234abcd-1234-1234-1234-abcde1234567"
        self.invalid_image_uuid = "abcd1234"
        dep_uuid = self.deployable_uuids[0]
        self.dep = fake_deployable.fake_deployable_obj(self.context,
                                                       uuid=dep_uuid)
        self.dev = fake_device.get_fake_devices_objs()[0]
        bdf = {"domain": "0000", "bus": "00", "device": "01", "function": "1"}
        self.cpid = {
            "id": 0,
            "uuid": "e4a66b0d-b377-40d6-9cdc-6bf7e720e596",
            "device_id": "1",
            "cpid_type": "PCI",
            "cpid_info": jsonutils.dumps(bdf).encode('utf-8')
        }

    @mock.patch('cyborg.objects.Device.get_by_device_id')
    @mock.patch('cyborg.objects.Deployable.get_cpid_list')
    @mock.patch('cyborg.objects.Deployable.get')
    @mock.patch('cyborg.agent.rpcapi.AgentAPI.fpga_program')
    def test_program_success(self, mock_program, mock_get_dep,
                             mock_get_cpid_list, mock_get_by_device_id):
        self.headers['X-Roles'] = 'admin'
        self.headers['Content-Type'] = 'application/json'
        dep_uuid = self.deployable_uuids[0]
        mock_get_dep.return_value = self.dep
        mock_get_by_device_id.return_value = self.dev
        mock_get_cpid_list.return_value = [self.cpid]
        mock_program.return_value = True
        body = [{"image_uuid": self.existent_image_uuid}]
        response = self.patch_json('/deployables/%s/program' % dep_uuid,
                                   [{'path': '/bitstream_id', 'value': body,
                                     'op': 'replace'}], headers=self.headers)
        self.assertEqual(HTTPStatus.OK, response.status_code)
        data = response.json_body
        self.assertEqual(dep_uuid, data['uuid'])

    @mock.patch('cyborg.objects.Device.get_by_device_id')
    @mock.patch('cyborg.objects.Deployable.get_cpid_list')
    @mock.patch('cyborg.objects.Deployable.get')
    @mock.patch('cyborg.agent.rpcapi.AgentAPI.fpga_program')
    def test_program_failed(self, mock_program, mock_get_dep,
                            mock_get_cpid_list, mock_get_by_device_id):
        self.headers['X-Roles'] = 'admin'
        self.headers['Content-Type'] = 'application/json'
        dep_uuid = self.deployable_uuids[0]
        mock_get_dep.return_value = self.dep
        mock_get_by_device_id.return_value = self.dev
        mock_get_cpid_list.return_value = [self.cpid]
        mock_program.return_value = False
        body = [{"image_uuid": self.existent_image_uuid}]
        try:
            self.patch_json('/deployables/%s/program' % dep_uuid,
                            [{'path': '/bitstream_id', 'value': body,
                              'op': 'replace'}], headers=self.headers)
        except Exception as e:
            exc = e
        self.assertIn(exception.FPGAProgramError(
                      ret=mock_program.return_value).args[0],
                      exc.args[0]
                      )

    @mock.patch('cyborg.objects.Device.get_by_device_id')
    @mock.patch('cyborg.objects.Deployable.get_cpid_list')
    @mock.patch('cyborg.objects.Deployable.get')
    @mock.patch('cyborg.agent.rpcapi.AgentAPI.fpga_program')
    def test_program_invalid_uuid(self, mock_program, mock_get_dep,
                                  mock_get_cpid_list, mock_get_by_device_id):
        self.headers['X-Roles'] = 'admin'
        self.headers['Content-Type'] = 'application/json'
        dep_uuid = self.deployable_uuids[0]
        mock_get_dep.return_value = self.dep
        mock_get_by_device_id.return_value = self.dev
        mock_get_cpid_list.return_value = [self.cpid]
        mock_program.return_value = False
        body = [{"image_uuid": self.invalid_image_uuid}]
        try:
            self.patch_json('/deployables/%s/program' % dep_uuid,
                            [{'path': '/bitstream_id',
                              'value': body,
                              'op': 'replace'}],
                            headers=self.headers)
        except Exception as e:
            exc = e
        self.assertIn(exception.InvalidUUID(self.invalid_image_uuid).args[0],
                      exc.args[0])

    @mock.patch('cyborg.objects.Device.get_by_device_id')
    @mock.patch('cyborg.objects.Deployable.get_cpid_list')
    @mock.patch('cyborg.objects.Deployable.get')
    @mock.patch('cyborg.agent.rpcapi.AgentAPI.fpga_program')
    def test_program_wrong_image_uuid(self, mock_program,
                                      mock_get_dep,
                                      mock_get_cpid_list,
                                      mock_get_by_device_id):
        self.headers['X-Roles'] = 'admin'
        self.headers['Content-Type'] = 'application/json'
        dep_uuid = self.deployable_uuids[0]
        mock_get_dep.return_value = self.dep
        mock_get_by_device_id.return_value = self.dev
        mock_get_cpid_list.return_value = [self.cpid]
        mock_program.return_value = False
        body = [{"image_uuid": self.nonexistent_image_uuid}]
        try:
            self.patch_json('/deployables/%s/program' % dep_uuid,
                            [{'path': '/bitstream_id',
                              'value': body,
                              'op': 'replace'}],
                            headers=self.headers)
        except Exception as e:
            exc = e
        self.assertIn(exception.FPGAProgramError(
                      ret=mock_program.return_value).args[0],
                      exc.args[0]
                      )
