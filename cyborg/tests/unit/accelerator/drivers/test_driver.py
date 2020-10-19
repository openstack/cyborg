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

from cyborg.accelerator.drivers.driver import GenericDriver
from cyborg.tests import base


class WellDoneDriver(GenericDriver):
    def discover(self):
        pass

    def update(self, control_path, image_path):
        pass

    def get_stats(self):
        pass


class NotCompleteDriver(GenericDriver):
    def discover(self):
        pass


class TestGenericDriver(base.TestCase):

    def test_generic_driver(self):
        # Can't instantiate abstract class NotCompleteDriver with
        # abstract methods get_stats, update
        result = self.assertRaises(TypeError, NotCompleteDriver)
        self.assertIn("Can't instantiate abstract class",
                      str(result))
