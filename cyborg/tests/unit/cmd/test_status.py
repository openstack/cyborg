# Copyright (c) 2018 NEC, Corp.
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

import fixtures
import os
import tempfile
import yaml

from oslo_config import cfg
from oslo_serialization import jsonutils
from oslo_upgradecheck import upgradecheck

from cyborg.cmd import status
from cyborg.common import authorize_wsgi
from cyborg.tests import base


class TestUpgradeCheckPolicyJSON(base.TestCase):

    def setUp(self):
        super(TestUpgradeCheckPolicyJSON, self).setUp()
        self.cmd = status.UpgradeCommands()
        authorize_wsgi.CONF.clear_override('policy_file', group='oslo_policy')
        self.data = {
            'rule_admin': 'True',
            'rule_admin2': 'is_admin:True'
        }
        self.temp_dir = self.useFixture(fixtures.TempDir())
        fd, self.json_file = tempfile.mkstemp(dir=self.temp_dir.path)
        fd, self.yaml_file = tempfile.mkstemp(dir=self.temp_dir.path)

        with open(self.json_file, 'w') as fh:
            jsonutils.dump(self.data, fh)
        with open(self.yaml_file, 'w') as fh:
            yaml.dump(self.data, fh)

        original_search_dirs = cfg._search_dirs

        def fake_search_dirs(dirs, name):
            dirs.append(self.temp_dir.path)
            return original_search_dirs(dirs, name)

        self.mock_search = self.useFixture(fixtures.MockPatch(
            'oslo_config.cfg._search_dirs')).mock
        self.mock_search.side_effect = fake_search_dirs

    def test_policy_json_file_fail_upgrade(self):
        # Test with policy json file full path set in config.
        self.flags(policy_file=self.json_file, group="oslo_policy")
        self.assertEqual(upgradecheck.Code.FAILURE,
                         self.cmd._check_policy_json().code)

    def test_policy_yaml_file_pass_upgrade(self):
        # Test with full policy yaml file path set in config.
        self.flags(policy_file=self.yaml_file, group="oslo_policy")
        self.assertEqual(upgradecheck.Code.SUCCESS,
                         self.cmd._check_policy_json().code)

    def test_no_policy_file_pass_upgrade(self):
        # Test with no policy file exist.
        self.assertEqual(upgradecheck.Code.SUCCESS,
                         self.cmd._check_policy_json().code)

    def test_default_policy_yaml_file_pass_upgrade(self):
        tmpfilename = os.path.join(self.temp_dir.path, 'policy.yaml')
        with open(tmpfilename, 'w') as fh:
            yaml.dump(self.data, fh)
        self.assertEqual(upgradecheck.Code.SUCCESS,
                         self.cmd._check_policy_json().code)

    def test_old_default_policy_json_file_fail_upgrade(self):
        self.flags(policy_file='policy.json', group="oslo_policy")
        tmpfilename = os.path.join(self.temp_dir.path, 'policy.json')
        with open(tmpfilename, 'w') as fh:
            jsonutils.dump(self.data, fh)
        self.assertEqual(upgradecheck.Code.FAILURE,
                         self.cmd._check_policy_json().code)
