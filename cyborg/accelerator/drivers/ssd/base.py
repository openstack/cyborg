# Copyright 2020 Inspur Electronic Information Industry Co.,LTD.
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
Cyborg Generic SSD driver implementation.
"""
from oslo_log import log as logging

from cyborg.accelerator.common import utils as pci_utils
from cyborg.accelerator.drivers.ssd import utils

LOG = logging.getLogger(__name__)
VENDOR_MAPS = pci_utils.get_vendor_maps()


class SSDDriver(object):
    """Generic class for SSD drivers.

       This is just a virtual SSD drivers interface.
       Vendor should implement their specific drivers.
    """

    @classmethod
    def create(cls, vendor=None, *args, **kwargs):
        if not vendor:
            return cls(*args, **kwargs)
        for sclass in cls.__subclasses__():
            vendor_name = VENDOR_MAPS.get(vendor, vendor)
            if vendor_name == sclass.VENDOR:
                return sclass(*args, **kwargs)
        raise LookupError("Not find the SSD driver for vendor %s" % vendor)

    def discover(self):
        """Discover SSD information of current vendor(Identified by class).

           If no vendor-specific driver provided, this will return all NVMe SSD
           devices
        :return: List of SSD information dict.
        """
        LOG.info('The method "discover" is called in generic.SSDDriver')
        devs = utils.discover_ssds()
        return devs

    @classmethod
    def discover_vendors(cls):
        """Discover SSD vendors of current node.

        :return: SSD vendor ID list.
        """
        return utils.discover_vendors()
