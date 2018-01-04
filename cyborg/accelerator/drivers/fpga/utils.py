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
Utils for FPGA driver.
"""

import glob
import re


VENDORS = ["intel"]  # can extend, such as ["intel", "xilinx"]

SYS_FPGA_PATH = "/sys/class/fpga"
VENDORS_PATTERN = re.compile("|".join(["(%s)" % v for v in VENDORS]))


def discover_vendors():
    vendors = set()
    for p in glob.glob1(SYS_FPGA_PATH, "*"):
        m = VENDORS_PATTERN.match(p)
        if m:
            vendors.add(m.group())
    return list(vendors)
