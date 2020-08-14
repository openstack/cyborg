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

from cyborg.api.controllers.v2 import versions
from cyborg.tests.unit.api.controllers.v2 import base as v2_test


class TestAPI(v2_test.APITestV2):

    def setUp(self):
        super(TestAPI, self).setUp()
        self.headers = self.gen_headers(self.context)

    def test_get_api_v2(self):
        data = self.get_json('/', headers=self.headers)
        self.assertEqual(data['status'], "CURRENT")
        self.assertEqual(data['max_version'], versions._MAX_VERSION_STRING)
        self.assertEqual(data['id'], "v2.0")
        result = isinstance(data['links'], list)
        self.assertTrue(result)
