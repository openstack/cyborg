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

"""Base class and helpers for API sample structural validation tests."""

import json
import os
import unittest

from unittest import mock

import fixtures
import pecan

from oslo_config import cfg
from oslo_utils import strutils

from cyborg.tests import base
from cyborg.tests.local_fixtures import capture
from cyborg.tests.local_fixtures import common
from cyborg.tests.local_fixtures import db_fixture


cfg.CONF.import_group('keystone_authtoken', 'keystonemiddleware.auth_token')

GENERATE_SAMPLES = strutils.bool_from_string(
    os.environ.get('GENERATE_SAMPLES', 'no')
)


def _structure(obj):
    """Reduce a JSON object to its structural skeleton.

    Dicts keep their keys; scalar values are replaced by their type
    name.  Lists are recursively reduced and sorted so element order
    does not matter.  None becomes mock.ANY so null fields in either
    the sample or response act as wildcards.
    """
    if obj is None:
        return mock.ANY
    if isinstance(obj, dict):
        return {k: _structure(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return sorted(
            [_structure(x) for x in obj],
            key=lambda x: json.dumps(x, sort_keys=True, default=repr),
        )
    return type(obj).__name__


class ApiSampleTestBase(base.TestCase):
    """Functional test base that boots a real Pecan app against SQLite."""

    def setUp(self):
        super().setUp()
        self._logging = self.useFixture(capture.Logging())
        self._warnings = self.useFixture(capture.WarningsFixture())
        db_fix = self.useFixture(db_fixture.DatabaseFixture())
        self._db = db_fix.dbapi
        self.app = common.make_app()
        self.addCleanup(pecan.set_config, {}, overwrite=True)

    def seed_devices(self):
        result = common.seed_devices(self.context)
        return {k: v.uuid for k, v in result.items()}

    def seed_device_profiles(self):
        result = common.seed_device_profiles(self.context)
        return {k: v.uuid for k, v in result.items()}

    def seed_arqs(self):
        self.useFixture(
            fixtures.MockPatch(
                'cyborg.objects.ext_arq.AgentAPI', autospec=True
            )
        )
        self.seed_device_profiles()
        result = common.seed_arqs(self.context, self._db)
        return {k: v.uuid for k, v in result.items()}

    def _get_headers(self, extra_headers=None):
        headers = {
            'X-User-Name': 'functional-test-user',
            'X-User-Id': 'functional-test-user',
            'X-Project-Name': 'functional-test-project',
            'X-Project-Id': 'functional-test-project',
            'X-User-Domain-Id': 'default',
            'X-User-Domain-Name': 'Default',
            'X-Auth-Token': 'functional-test-token',
            'X-Roles': 'admin',
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _check_sample(self, url, sample_path, extra_headers=None):
        """Compare API response structure against a sample JSON file.

        When GENERATE_SAMPLES=1, overwrites the sample file instead.
        """
        response = self.app.get(
            url, headers=self._get_headers(extra_headers), expect_errors=False
        )
        actual = response.json

        if GENERATE_SAMPLES:
            sample_dir = os.path.dirname(sample_path)
            if not os.path.isdir(sample_dir):
                os.makedirs(sample_dir)
            with open(sample_path, 'w') as f:
                json.dump(actual, f, indent=4, sort_keys=True)
                f.write('\n')
            return

        with open(sample_path) as f:
            expected = json.load(f)

        self.assertEqual(
            _structure(expected),
            _structure(actual),
            f'Sample path: {os.path.normpath(sample_path)}',
        )


class TestStructure(unittest.TestCase):
    """Negative tests for the _structure helper."""

    def test_matching_structures(self):
        a = {'name': 'foo', 'count': 1, 'tags': ['a', 'b']}
        b = {'name': 'bar', 'count': 9, 'tags': ['x', 'y']}
        self.assertEqual(_structure(a), _structure(b))

    def test_missing_key(self):
        a = {'name': 'foo', 'count': 1}
        b = {'name': 'bar'}
        self.assertNotEqual(_structure(a), _structure(b))

    def test_extra_key(self):
        a = {'name': 'foo'}
        b = {'name': 'bar', 'extra': True}
        self.assertNotEqual(_structure(a), _structure(b))

    def test_type_mismatch(self):
        a = {'value': 'string'}
        b = {'value': 42}
        self.assertNotEqual(_structure(a), _structure(b))

    def test_list_length_mismatch(self):
        a = {'items': [1, 2]}
        b = {'items': [1]}
        self.assertNotEqual(_structure(a), _structure(b))

    def test_list_order_independent(self):
        a = {'items': [{'a': 1}, {'b': 'x'}]}
        b = {'items': [{'b': 'y'}, {'a': 2}]}
        self.assertEqual(_structure(a), _structure(b))

    def test_null_matches_any_type(self):
        a = {'updated_at': None}
        b = {'updated_at': '2020-01-01'}
        self.assertEqual(_structure(a), _structure(b))
        self.assertEqual(_structure(b), _structure(a))
