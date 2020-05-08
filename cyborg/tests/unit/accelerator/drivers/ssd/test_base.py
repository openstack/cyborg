# Copyright 2020 Inspur Electronic Information Industry Co.,LTD..
#
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


from cyborg.accelerator.drivers.ssd.base import SSDDriver
from cyborg.accelerator.drivers.ssd.inspur.driver import InspurNVMeSSDDriver
from cyborg.tests import base


class TestSSDDriver(base.TestCase):
    def test_create_base_ssd_driver(self):
        drv = SSDDriver.create()
        self.assertIsInstance(drv, SSDDriver)
        self.assertNotIsInstance(drv, InspurNVMeSSDDriver)

    def test_create_inspur_ssd_driver(self):
        drv = SSDDriver.create(vendor='inspur')
        self.assertIsInstance(drv, InspurNVMeSSDDriver)

    def test_create_ssd_vendor_not_found(self):
        self.assertRaises(LookupError, SSDDriver.create, '_non-exist_vendor')
