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
Cyborg NIC driver implementation.
"""

VENDOR_MAPS = {"0x8086": "intel"}


class NICDriver(object):
    """Base class for Nic drivers.

       This is just a virtual NIC drivers interface.
       Vendor should implement their specific drivers.
    """

    @classmethod
    def create(cls, vendor, *args, **kwargs):
        for sclass in cls.__subclasses__():
            vendor_name = VENDOR_MAPS.get(vendor, vendor)
            if vendor_name == sclass.VENDOR:
                return sclass(*args, **kwargs)
        raise LookupError("Not find the NIC driver for vendor %s" % vendor)

    def discover(self):
        """Discover NIC information of current vendor(Identified by class).

        :return: List of NIC information dict.
        """
        raise NotImplementedError()

    @classmethod
    def discover_vendors(cls):
        """Discover NIC vendors of current node.

        :return: NIC vendor ID list.
        """
        raise NotImplementedError()
