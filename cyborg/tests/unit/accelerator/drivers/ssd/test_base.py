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


from unittest import mock

from cyborg.accelerator.drivers.ssd import base as ssd_base
from cyborg.accelerator.drivers.ssd.inspur import driver
from cyborg.tests import base


class TestSSDDriver(base.TestCase):
    def test_create_base_ssd_driver(self):
        drv = ssd_base.SSDDriver.create()
        self.assertIsInstance(drv, ssd_base.SSDDriver)
        self.assertNotIsInstance(drv, driver.InspurNVMeSSDDriver)

    def test_create_inspur_ssd_driver(self):
        drv = ssd_base.SSDDriver.create(vendor='inspur')
        self.assertIsInstance(drv, driver.InspurNVMeSSDDriver)

    def test_create_ssd_vendor_not_found(self):
        self.assertRaises(
            LookupError, ssd_base.SSDDriver.create, '_non-exist_vendor'
        )

    def test_init_host_default_noop(self):
        drv = ssd_base.SSDDriver()
        drv.init_host()

    def test_cleanup_default_noop(self):
        drv = ssd_base.SSDDriver()
        drv.cleanup(mock.Mock())
