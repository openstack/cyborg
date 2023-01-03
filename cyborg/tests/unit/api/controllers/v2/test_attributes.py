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

from unittest import mock

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
        self.assertTrue(len(out_attributes), len(attributes))
