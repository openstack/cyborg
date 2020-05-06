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


from cyborg.accelerator.drivers.qat.base import QATDriver
from cyborg.tests import base


class TestQATDriver(base.TestCase):
    def test_create(self):
        QATDriver.create("intel")
        self.assertRaises(LookupError, QATDriver.create, "other")

    def test_discover(self):
        d = QATDriver()
        self.assertRaises(NotImplementedError, d.discover)

    def test_discover_vendors(self):
        d = QATDriver()
        self.assertRaises(NotImplementedError, d.discover_vendors)
