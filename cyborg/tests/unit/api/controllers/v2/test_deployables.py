# Copyright 2020 Intel, Inc.
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
from cyborg.tests.unit import fake_deployable


class TestDeployablesController(v2_test.APITestV2):

    DEPLOYABLE_URL = '/deployables'

    def setUp(self):
        super(TestDeployablesController, self).setUp()
        self.headers = self.gen_headers(self.context)
        self.fake_deployable = fake_deployable.fake_deployable_obj(
            self.context)

    def _validate_links(self, links, deployable_uuid):
        has_self_link = False
        for link in links:
            if link['rel'] == 'self':
                has_self_link = True
                url = link['href']
                components = url.split('/')
                self.assertEqual(components[-1], deployable_uuid)
        self.assertTrue(has_self_link)

    def _validate_deployable(self, in_deployable, out_deployable):
        for field in in_deployable.keys():
            if field != 'id':
                self.assertEqual(in_deployable[field], out_deployable[field])
        # Check that the link is properly set up
        self._validate_links(out_deployable['links'], in_deployable['uuid'])

    @mock.patch('cyborg.objects.Deployable.get')
    def test_get_one_by_uuid(self, mock_deployable):
        in_deployable = self.fake_deployable
        mock_deployable.return_value = in_deployable
        uuid = in_deployable['uuid']

        url = self.DEPLOYABLE_URL + '/%s'
        out_deployable = self.get_json(url % uuid, headers=self.headers)
        mock_deployable.assert_called_once()
        self._validate_deployable(in_deployable, out_deployable)

    @mock.patch('cyborg.objects.Deployable.list')
    def test_get_all(self, mock_deployables):
        mock_deployables.return_value = [self.fake_deployable]
        data = self.get_json(self.DEPLOYABLE_URL, headers=self.headers)
        out_deployable = data['deployables']
        self.assertIsInstance(out_deployable, list)
        for out_dev in out_deployable:
            self.assertIsInstance(out_dev, dict)
        self.assertTrue(len(out_deployable), 1)
        self._validate_deployable(self.fake_deployable, out_deployable[0])

    @mock.patch('cyborg.objects.Deployable.list')
    def test_get_with_filters(self, mock_deployables):
        mock_deployables.return_value = [self.fake_deployable]
        # TODO(Xinran) Add API doc to explain the usage of filter.
        # Add "?filters.field=limit&filters.value=1" in DEPLOYABLE_URL, in
        # order to list the deployables with limited number which is 1.
        data = self.get_json(
            self.DEPLOYABLE_URL + "?filters.field=limit&filters.value=1",
            headers=self.headers)
        out_deployable = data['deployables']
        mock_deployables.assert_called_once_with(mock.ANY,
                                                 filters={"limit": "1"})
        self._validate_deployable(self.fake_deployable, out_deployable[0])

    @mock.patch('cyborg.objects.Deployable.list')
    def test_get_with_filters_not_match(self, mock_deployables):
        # This will return null list because the fake deployable's name
        # is "dp_name".
        mock_deployables.return_value = []
        data = self.get_json(
            self.DEPLOYABLE_URL +
            "?filters.field=name&filters.value=wrongname",
            headers=self.headers)
        out_deployable = data['deployables']
        mock_deployables.assert_called_once_with(mock.ANY,
                                                 filters={"name": "wrongname"})
        self.assertEqual(len(out_deployable), 0)
