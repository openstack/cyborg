#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re

import os_resource_classes as orc
from oslo_serialization import jsonutils

from cyborg.accelerator.drivers.driver import GenericDriver
from cyborg.common import constants
from cyborg.conf import CONF
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_attribute
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device


class FakeDriver(GenericDriver):
    """Base class for Fake drivers.

       This is just a Fake drivers interface.
    """
    VENDOR = "fake"
    NUM_ACCELERATORS = 16

    def _generate_controlpath_id(self, pci):
        driver_cpid = driver_controlpath_id.DriverControlPathID()
        driver_cpid.cpid_type = "PCI"
        driver_cpid.cpid_info = pci["slot"]
        return driver_cpid

    def _generate_attach_handles(self, pci, num_accelerators):
        """Returns list of attach handles, with same bus# but
        differing in device/function numbers. Assumes
        NUM_ACCELERATORS <= 256, otherwise bus# has to change too.
        """
        # In PCI bus-device-function address, 1 device can have 8 functions.
        NUM_PCI_FN_PER_PCI_DEVICE = 8

        ah_list = []
        for fn in range(1, num_accelerators + 1):  # fn 0 is CPID
            driver_ah = driver_attach_handle.DriverAttachHandle()
            # The virt driver will ignore this type when attaching
            driver_ah.attach_type = constants.AH_TYPE_TEST_PCI
            driver_ah.in_use = False

            pci_slot_dict = jsonutils.loads(pci['slot'])
            pci_slot_dict['device'] = str(int(fn / NUM_PCI_FN_PER_PCI_DEVICE))
            pci_slot_dict['function'] = str(fn % NUM_PCI_FN_PER_PCI_DEVICE)
            pci_slot_str = jsonutils.dumps(pci_slot_dict)

            driver_ah.attach_info = pci_slot_str
            ah_list.append(driver_ah)
        return ah_list

    def _generate_attribute_list(self):
        attr_traits = driver_attribute.DriverAttribute()
        attr_traits.key = "traits1"
        attr_traits.value = "CUSTOM_FAKE_DEVICE"
        attr_rc = driver_attribute.DriverAttribute()
        attr_rc.key = "rc"
        attr_rc.value = orc.FPGA
        return [attr_traits, attr_rc]

    def _generate_dep_list(self, pci):
        driver_dep = driver_deployable.DriverDeployable()
        driver_dep.attach_handle_list = self._generate_attach_handles(
            pci, self.NUM_ACCELERATORS)
        # NOTE(sean-k-mooney): we need to prepend the host name to the
        # device name as this is used to generate the RP name and uuid in
        # the cyborg conductor when updating placement. As such this needs
        # to be unique per host to allow multi node testing with the fake
        # driver.
        name = "%s_%s" % (CONF.host, pci.get('device'))
        # Replace any non alphanumeric, hyphen or underscore character with
        # underscore to comply with placement RP name requirements
        driver_dep.name = re.sub(r"(?![a-zA-Z0-9_\-]).", "_", name)
        driver_dep.driver_name = 'fake'
        driver_dep.num_accelerators = self.NUM_ACCELERATORS
        driver_dep.attribute_list = self._generate_attribute_list()
        return [driver_dep]

    def discover(self):
        fpga_list = []
        pci_addr = '{"domain":"0000","bus":"0c","device":"00","function":"0"}'
        pci_dict = {
            'slot': pci_addr,                    # PCI slot address
            'device': 'FakeDevice',              # Name of the device
            'vendor_id': '0xABCD',                 # ID of the vendor
            'class': 'Fake class',               # Name of the class
            'device_id': '0xabcd'                 # ID of the device
        }
        device = driver_device.DriverDevice()
        device.vendor = pci_dict["vendor_id"]
        device.model = pci_dict.get('model', 'miss model info')
        std_board_info = {'device_id': pci_dict.get('device_id', None),
                          'class': pci_dict.get('class', None)}
        device.std_board_info = jsonutils.dumps(std_board_info)
        device.vendor_board_info = 'fake_vendor_info'
        device.type = constants.DEVICE_FPGA
        device.stub = False
        device.controlpath_id = self._generate_controlpath_id(pci_dict)
        device.deployable_list = self._generate_dep_list(pci_dict)
        fpga_list.append(device)
        return fpga_list

    def update(self, control_path, image_path):
        return True

    def get_stats(self):
        return {}
