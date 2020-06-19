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

from unittest import mock

from cyborg.tests.unit.api.controllers.v2 import base as v2_test
from cyborg.tests.unit import fake_device


class TestDevicesController(v2_test.APITestV2):

    DEVICE_URL = '/devices'

    def setUp(self):
        super(TestDevicesController, self).setUp()
        self.headers = self.gen_headers(self.context)
        self.fake_devices = fake_device.get_fake_devices_objs()

    def _validate_links(self, links, device_uuid):
        has_self_link = False
        for link in links:
            if link['rel'] == 'self':
                has_self_link = True
                url = link['href']
                components = url.split('/')
                self.assertEqual(components[-1], device_uuid)
        self.assertTrue(has_self_link)

    def _validate_device(self, in_device, out_device):
        for field in in_device.keys():
            if field != 'id':
                self.assertEqual(in_device[field], out_device[field])
        # Check that the link is properly set up
        self._validate_links(out_device['links'], in_device['uuid'])

    @mock.patch('cyborg.objects.Device.get')
    def test_get_one_by_uuid(self, mock_device):
        in_device = self.fake_devices[0]
        mock_device.return_value = in_device
        uuid = in_device['uuid']

        url = self.DEVICE_URL + '/%s'
        out_device = self.get_json(url % uuid, headers=self.headers)
        mock_device.assert_called_once()
        self._validate_device(in_device, out_device)

    @mock.patch('cyborg.objects.Device.list')
    def test_get_all(self, mock_devices):
        mock_devices.return_value = self.fake_devices
        data = self.get_json(self.DEVICE_URL, headers=self.headers)
        out_devices = data['devices']
        self.assertIsInstance(out_devices, list)
        for out_dev in out_devices:
            self.assertIsInstance(out_dev, dict)
        self.assertTrue(len(out_devices), len(self.fake_devices))
        for in_device, out_device in zip(self.fake_devices, out_devices):
            self._validate_device(in_device, out_device)

    @mock.patch('cyborg.objects.Device.list')
    def test_get_with_filters(self, mock_devices):
        in_devices = self.fake_devices
        mock_devices.return_value = in_devices[:1]
        data = self.get_json(
            self.DEVICE_URL + "?filters.field=limit&filters.value=1",
            headers=self.headers)
        out_devices = data['devices']
        mock_devices.assert_called_once_with(mock.ANY, filters={"limit": "1"})
        for in_device, out_device in zip(self.fake_devices, out_devices):
            self._validate_device(in_device, out_device)

    @mock.patch('cyborg.objects.Device.list')
    def test_get_by_type(self, mock_devices):
        in_devices = self.fake_devices
        mock_devices.return_value = [in_devices[0]]
        data = self.get_json(
            self.DEVICE_URL + "?type=FPGA",
            headers=self.headers)
        out_devices = data['devices']
        mock_devices.assert_called_once_with(mock.ANY,
                                             filters={"type": "FPGA"})
        for in_device, out_device in zip(self.fake_devices, out_devices):
            self._validate_device(in_device, out_device)

    @mock.patch('cyborg.objects.Device.list')
    def test_get_by_vendor(self, mock_devices):
        in_devices = self.fake_devices
        mock_devices.return_value = [in_devices[0]]
        data = self.get_json(
            self.DEVICE_URL + "?vendor=0xABCD",
            headers=self.headers)
        out_devices = data['devices']
        mock_devices.assert_called_once_with(mock.ANY,
                                             filters={"vendor": "0xABCD"})
        for in_device, out_device in zip(self.fake_devices, out_devices):
            self._validate_device(in_device, out_device)

    @mock.patch('cyborg.objects.Device.list')
    def test_get_by_hostname(self, mock_devices):
        in_devices = self.fake_devices
        mock_devices.return_value = [in_devices[0]]
        data = self.get_json(
            self.DEVICE_URL + "?hostname=test-node-1",
            headers=self.headers)
        out_devices = data['devices']
        mock_devices.assert_called_once_with(
            mock.ANY, filters={"hostname": "test-node-1"})
        for in_device, out_device in zip(self.fake_devices, out_devices):
            self._validate_device(in_device, out_device)
