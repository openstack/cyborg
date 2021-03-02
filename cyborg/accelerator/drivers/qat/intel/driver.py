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
Cyborg Intel QAT driver implementation.
"""

from cyborg.accelerator.drivers.qat.base import QATDriver
from cyborg.accelerator.drivers.qat.intel import sysinfo


class IntelQATDriver(QATDriver):
    """Class for Intel QAT drivers.
       Vendor should implement their specific drivers in this class.
    """
    VENDOR = "intel"

    def __init__(self, *args, **kwargs):
        pass

    def discover(self):
        return sysinfo.qat_tree()
