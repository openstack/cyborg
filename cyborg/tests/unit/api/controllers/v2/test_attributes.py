# Copyright 2023 Inspur, Inc.
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

from http import HTTPStatus
from unittest import mock

from oslo_serialization import jsonutils

from cyborg.tests.unit.api.controllers.v2 import base as v2_test
from cyborg.tests.unit import fake_attribute


class TestAttributes(v2_test.APITestV2):
    ATTRIBUTE_URL = '/attributes'

    def setUp(self):
        super(TestAttributes, self).setUp()
        self.headers = self.gen_headers(self.context)
        self.fake_attributes = fake_attribute.fake_db_attribute()
        self.fake_attribute_objs = \
            [fake_attribute.fake_attribute_obj(self.context)]

    def _validate_links(self, links, attribute_uuid):
        has_self_link = False
        for link in links:
            if link['rel'] == 'self':
                has_self_link = True
                url = link['href']
                components = url.split('/')
                self.assertEqual(components[-1], attribute_uuid)
        self.assertTrue(has_self_link)

    def _validate_attributes(self, in_attributes, out_attributes):
        self.assertEqual(in_attributes['uuid'], out_attributes['uuid'])
        self.assertEqual(in_attributes['key'], out_attributes['key'])
        self.assertEqual(in_attributes['value'], out_attributes['value'])
        self.assertEqual(in_attributes['deployable_id'],
                         out_attributes['deployable_id'])

        # Check that the link is properly set up
        self._validate_links(out_attributes['links'], in_attributes['uuid'])

    @mock.patch('cyborg.objects.Attribute.get')
    def test_get_one_by_uuid(self, mock_attributes_uuid):
        attribute = self.fake_attribute_objs[0]
        mock_attributes_uuid.return_value = attribute
        url = self.ATTRIBUTE_URL + '/%s'
        out_attribute = self.get_json(url % attribute['uuid'],
                                      headers=self.headers)
        mock_attributes_uuid.assert_called_once()
        self._validate_attributes(attribute, out_attribute)

    @mock.patch('cyborg.objects.Attribute.get_by_filter')
    def test_get_attribute_by_deployable_id(self, mock_deployable_id):
        attributes = self.fake_attribute_objs
        mock_deployable_id.return_value = attributes
        deployable_id = attributes[0]['deployable_id']
        url = self.ATTRIBUTE_URL + "?deployable_id=" + str(deployable_id)
        out_attributes = self.get_json(url, headers=self.headers)
        mock_deployable_id.assert_called_once()
        self.assertEqual(len(out_attributes), len(attributes))

    @mock.patch('cyborg.objects.Attribute.get_by_filter')
    def test_get_all(self, mock_attributes):
        mock_attributes.return_value = self.fake_attribute_objs
        data = self.get_json(self.ATTRIBUTE_URL, headers=self.headers)
        out_attributes = data['attributes']
        self.assertIsInstance(out_attributes, list)
        self.assertEqual(len(out_attributes), len(self.fake_attribute_objs))
        for in_attribute, out_attribute in zip(self.fake_attribute_objs,
                                               out_attributes):
            self._validate_attributes(in_attribute, out_attribute)

    @mock.patch('cyborg.objects.Attribute.get_by_filter')
    def test_get_attribute_by_key(self, mock_key):
        attributes = self.fake_attribute_objs
        mock_key.return_value = attributes
        url = self.ATTRIBUTE_URL + "?key=" + attributes[0]['key']
        out_attributes = self.get_json(url, headers=self.headers)
        mock_key.assert_called_once()
        self.assertEqual(len(out_attributes), len(attributes))

    @mock.patch('cyborg.objects.Attribute.create')
    def test_create(self, mock_cond_attribute):
        mock_cond_attribute.return_value = self.fake_attribute_objs[0]
        response = self.post_json(self.ATTRIBUTE_URL, self.fake_attributes,
                                  headers=self.headers)
        out_attribute = jsonutils.loads(response.controller_output)
        self.assertEqual(HTTPStatus.CREATED, response.status_int)
        self._validate_attributes(self.fake_attribute_objs[0], out_attribute)

    @mock.patch('cyborg.objects.Attribute.get_by_filter')
    def test_get_all_by_deployable_id_and_key(self, mock_attribute):
        attributes = self.fake_attribute_objs
        mock_attribute.return_value = attributes
        dp_url = "?deployable_id=" + str(attributes[0]['deployable_id'])
        url = self.ATTRIBUTE_URL + dp_url + "&key=" + attributes[0]['key']
        data = self.get_json(url, headers=self.headers)
        out_attributes = data['attributes']
        mock_attribute.assert_called_once()
        self.assertEqual(len(out_attributes), len(attributes))
        for in_attribute, out_attribute in zip(attributes, out_attributes):
            self._validate_attributes(in_attribute, out_attribute)

    @mock.patch('cyborg.objects.Attribute.get')
    @mock.patch('cyborg.objects.Attribute.destroy')
    def test_delete(self, mock_attribute_delete, mock_attribute):
        uuid = self.fake_attribute_objs[0]['uuid']
        # Delete by UUID
        url = self.ATTRIBUTE_URL + '/%s' % uuid
        response = self.delete(url, headers=self.headers)
        self.assertEqual(HTTPStatus.NO_CONTENT, response.status_int)
