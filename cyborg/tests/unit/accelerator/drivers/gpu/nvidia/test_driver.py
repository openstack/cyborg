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

from cyborg.accelerator.drivers.gpu.nvidia import sysinfo
from cyborg.common import exception
from cyborg.conf import devices as conf_devices
from cyborg.tests import base


class TestNvidiaGPUDriver(base.TestCase):
    def _enable_vgpu_type(self, vgpu_type, device_addresses):
        self.cfg_fixture.config(
            enabled_vgpu_types=[vgpu_type], group="gpu_devices"
        )
        conf_devices.register_dynamic_opts(sysinfo.CONF)
        self.cfg_fixture.config(
            device_addresses=device_addresses,
            group="vgpu_%s" % vgpu_type,
        )

    def test_get_supported_vgpu_types_case_insensitive_duplicate(self):
        # Two vgpu types configured with the same physical address, but
        # written in different case, must still be caught as a duplicate
        # rather than silently accepted as two distinct devices.
        self.cfg_fixture.config(
            enabled_vgpu_types=["nvidia-35", "nvidia-36"],
            group="gpu_devices",
        )
        conf_devices.register_dynamic_opts(sysinfo.CONF)
        self.cfg_fixture.config(
            device_addresses=["0000:AF:00.0"], group="vgpu_nvidia-35"
        )
        self.cfg_fixture.config(
            device_addresses=["0000:af:00.0"], group="vgpu_nvidia-36"
        )
        self.assertRaises(
            exception.InvalidvGPUConfig, sysinfo._get_supported_vgpu_types
        )

    def test_get_vgpu_type_per_pgpu_case_insensitive(self):
        # The operator wrote the address in uppercase in config; the
        # discovered pGPU address (as reported by the driver) is lowercase.
        # This must still resolve to a vGPU type instead of silently
        # falling through to pGPU (passthrough) registration.
        self._enable_vgpu_type("nvidia-35", ["0000:AF:00.0"])
        supported, mapping = sysinfo._get_supported_vgpu_types()
        vgpu_type = sysinfo._get_vgpu_type_per_pgpu(
            "0000:af:00.0", supported, mapping
        )
        self.assertEqual("nvidia-35", vgpu_type)

    def test_get_vgpu_type_per_pgpu_no_match(self):
        # An address that isn't configured for any vgpu type resolves to
        # None (falls back to pGPU registration), same as before this fix.
        self._enable_vgpu_type("nvidia-35", ["0000:AF:00.0"])
        supported, mapping = sysinfo._get_supported_vgpu_types()
        vgpu_type = sysinfo._get_vgpu_type_per_pgpu(
            "0000:ff:00.0", supported, mapping
        )
        self.assertIsNone(vgpu_type)
