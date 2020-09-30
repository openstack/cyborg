# Copyright 2020 Intel, Inc.
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
Cyborg Intel NIC driver implementation.
"""

from cyborg.accelerator.drivers.nic.base import NICDriver
from cyborg.accelerator.drivers.nic.intel import sysinfo


class IntelNICDriver(NICDriver):
    """Class for Intel NIC drivers.
       Vendor should implement their specific drivers in this class.
    """
    VENDOR = "intel"

    def __init__(self, *args, **kwargs):
        pass

    def discover(self):
        return sysinfo.nic_tree()
