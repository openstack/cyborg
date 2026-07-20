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
Cyborg FPGA driver implementation.
"""

from cyborg.accelerator.drivers import driver
from cyborg.accelerator.drivers.fpga import utils


class FPGADriver(driver.GenericDriver):
    """Base class for FPGA drivers.

    This is just a virtual FPGA drivers interface.
    Vendor should implement their specific drivers.
    """

    def init_host(self):
        pass

    def cleanup(self, device):
        pass

    def discover(self):
        raise NotImplementedError()

    def update(self, control_path, image_path):
        """Update the device firmware with a specific image.

        :param control_path: the control path of the device.
        :param image_path: path to the firmware image file.
        :returns: True if successful, False otherwise.
        """
        raise NotImplementedError()

    def get_stats(self):
        return {}

    @classmethod
    def discover_vendors(cls):
        return utils.discover_vendors()
