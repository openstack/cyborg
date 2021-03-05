# Copyright 2020 Inspur, Inc.
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
Cyborg Inspur FPGA driver implementation.
"""

from oslo_log import log as logging

from cyborg.accelerator.drivers.fpga.base import FPGADriver
from cyborg.accelerator.drivers.fpga.inspur import sysinfo

LOG = logging.getLogger(__name__)


class InspurFPGADriver(FPGADriver):
    """Class for Inspur FPGA drivers.
       Vendor should implement their specific drivers in this class.
    """
    VENDOR = "inspur"

    def __init__(self, *args, **kwargs):
        pass

    def discover(self):
        return sysinfo.fpga_tree()
