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


"""
Cyborg Intel FPGA driver implementation.
"""

import subprocess

from cyborg.accelerator.drivers.fpga.base import FPGADriver
from cyborg.accelerator.drivers.fpga.intel import sysinfo


class IntelFPGADriver(FPGADriver):
    """Base class for FPGA drivers.

       This is just a virtual FPGA drivers interface.
       Vedor should implement their specific drivers.
    """
    VENDOR = "intel"

    def __init__(self, *args, **kwargs):
        pass

    def discover(self):
        return sysinfo.fpga_tree()

    def program(self, device_path, image):
        bdf = ""
        path = sysinfo.find_pf_by_vf(device_path) if sysinfo.is_vf(
            device_path) else device_path
        if sysinfo.is_bdf(device_path):
            bdf = sysinfo.get_pf_bdf(device_path)
        else:
            bdf = sysinfo.get_bdf_by_path(path)
        bdfs = sysinfo.split_bdf(bdf)
        cmd = ["sudo", "fpgaconf"]
        for i in zip(["-b", "-d", "-f"], bdfs):
            cmd.extend(i)
        cmd.append(image)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        # FIXME Should log p.communicate(), p.stderr
        p.wait()
        return p.returncode
