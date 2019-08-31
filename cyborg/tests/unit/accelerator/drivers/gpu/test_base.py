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


from cyborg.accelerator.drivers.gpu.base import GPUDriver
from cyborg.accelerator.drivers.gpu.nvidia.driver import NVIDIAGPUDriver
from cyborg.tests import base


class TestGPUDriver(base.TestCase):
    def test_create(self):
        # NVIDIAGPUDriver.VENDOR == 'nvidia'
        GPUDriver.create(NVIDIAGPUDriver.VENDOR)
        self.assertRaises(LookupError, GPUDriver.create, "matrox")

    def test_discover(self):
        d = GPUDriver()
        self.assertRaises(NotImplementedError, d.discover)
