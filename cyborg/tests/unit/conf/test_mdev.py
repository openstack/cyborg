# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Tests for cyborg.conf.mdev configuration options."""

from oslo_config import cfg

from cyborg.conf import mdev
from cyborg.tests import base


CONF = cfg.CONF


class TestMdevConfigGroup(base.TestCase):
    """Tests for the [mdev] configuration group."""

    def test_device_spec_defaults_to_empty_list(self):
        """Verify CONF.mdev.device_spec defaults to []."""
        self.assertEqual([], CONF.mdev.device_spec)

    def test_device_spec_single_value(self):
        """Verify a single device_spec value can be set."""
        spec = ['{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}']
        self.flags(device_spec=spec, group='mdev')
        self.assertEqual(spec, CONF.mdev.device_spec)

    def test_device_spec_multi_value(self):
        """Verify multiple device_spec values can be set."""
        specs = [
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            '{"address": "*", "mdev_type": "nvidia-319", "max_instances": 8}',
        ]
        self.flags(device_spec=specs, group='mdev')
        self.assertEqual(specs, CONF.mdev.device_spec)

    def test_device_spec_in_list_opts(self):
        """Verify device_spec appears in list_opts() output."""
        opts = mdev.list_opts()
        self.assertIn(mdev.mdev_group, opts)
        opt_names = [o.name for o in opts[mdev.mdev_group]]
        self.assertIn('device_spec', opt_names)
