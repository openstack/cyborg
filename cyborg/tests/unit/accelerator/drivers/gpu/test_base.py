# Copyright 2018 Beijing Lenovo Software Ltd.
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

from cyborg.accelerator.drivers.gpu import base as gpu_base
from cyborg.accelerator.drivers.gpu.nvidia import driver
from cyborg.tests import base


class TestGPUDriver(base.TestCase):
    def test_create(self):
        # NVIDIAGPUDriver.VENDOR == 'nvidia'
        gpu_base.GPUDriver.create(driver.NVIDIAGPUDriver.VENDOR)
        self.assertRaises(LookupError, gpu_base.GPUDriver.create, "matrox")

    def test_discover(self):
        d = gpu_base.GPUDriver()
        self.assertRaises(NotImplementedError, d.discover)

    def test_init_host_default_noop(self):
        d = gpu_base.GPUDriver()
        d.init_host()

    def test_cleanup_default_noop(self):
        d = gpu_base.GPUDriver()
        d.cleanup(mock.Mock())
