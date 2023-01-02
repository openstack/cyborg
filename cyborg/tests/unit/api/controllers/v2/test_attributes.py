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

from cyborg.tests.unit.api.controllers.v2 import base as v2_test


class TestAttributes(v2_test.APITestV2):

    def setUp(self):
        super(TestAttributes, self).setUp()

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
