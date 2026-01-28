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

from cyborg.accelerator.drivers.pci import utils
from cyborg.tests import base


class TestVendorMaps(base.DietTestCase):
    """Tests for the VENDOR_MAPS dictionary in pci utils."""

    def test_vendor_maps_contains_all_expected(self):
        expected = {
            "10de": "nvidia",
            "102b": "matrox",
            "8086": "intel",
            "1bd4": "inspur",
            "10ee": "xilinx",
            "19e5": "huawei",
        }
        self.assertEqual(expected, utils.VENDOR_MAPS)

    def test_vendor_maps_unknown_returns_none(self):
        self.assertIsNone(utils.VENDOR_MAPS.get('ffff'))
