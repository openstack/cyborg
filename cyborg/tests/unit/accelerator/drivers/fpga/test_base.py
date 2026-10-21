# Copyright 2018 Intel, Inc.
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

from cyborg.accelerator.drivers.fpga import base as fpga_base
from cyborg.tests import base


class TestFPGADriver(base.TestCase):
    def test_discover(self):
        d = fpga_base.FPGADriver()
        self.assertRaises(NotImplementedError, d.discover)

    def test_update(self):
        d = fpga_base.FPGADriver()
        self.assertRaises(NotImplementedError, d.update, "path", "image")

    def test_init_host_default_noop(self):
        d = fpga_base.FPGADriver()
        d.init_host()

    def test_cleanup_default_noop(self):
        d = fpga_base.FPGADriver()
        d.cleanup(mock.Mock())
