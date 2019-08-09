from cyborg.accelerator.drivers.driver import GenericDriver
from cyborg.objects.driver_objects import driver_deployable, driver_device, \
    driver_attach_handle, driver_controlpath_id, driver_attribute

from cyborg.agent import rc_fields
from cyborg.common import constants

import os_resource_classes as orc
from oslo_serialization import jsonutils


class FakeDriver(GenericDriver):
    """Base class for Fake drivers.

       This is just a Fake drivers interface.
    """
    VENDOR = "fake"

    def _generate_controlpath_id(self, pci):
        driver_cpid = driver_controlpath_id.DriverControlPathID()
        driver_cpid.cpid_type = "PCI"
        driver_cpid.cpid_info = pci["slot"]
        return driver_cpid

    def _generate_attach_handle(self, pci):
        driver_ah = driver_attach_handle.DriverAttachHandle()
        # The virt driver will ignore this type when attaching
        driver_ah.attach_type = "fake"
        driver_ah.in_use = False
        driver_ah.attach_info = pci["slot"]
        return driver_ah

    def _generate_attribute_list(self):
        attr_traits = driver_attribute.DriverAttribute()
        attr_traits.key = "traits1"
        attr_traits.value = "CUSTOM_FAKE_DEVICE"
        attr_rc = driver_attribute.DriverAttribute()
        attr_rc.key = "rc"
        attr_rc.value = rc_fields.ResourceClass.normalize_name(
            rc_fields.ResourceClass.FPGA)
        return [attr_traits, attr_rc]

    def _generate_dep_list(self, pci):
        driver_dep = driver_deployable.DriverDeployable()
        driver_dep.attach_handle_list = [self._generate_attach_handle(pci)]
        driver_dep.name = pci.get('device')
        driver_dep.num_accelerators = 1
        driver_dep.attribute_list = self._generate_attribute_list()
        return [driver_dep]

    def discover(self):
        npu_list = []
        pci_addr = '{"domain":"0000","bus":"0c","device":"00","function":"0"}'
        pci_dict = {
            'slot': pci_addr,                    # PCI slot address
            'device': 'FakeDevice',              # Name of the device
            'vendor_id': 'fake',                 # ID of the vendor
            'class': 'Fake class',               # Name of the class
            'device_id': 'fake',                 # ID of the device
            'revision': '20'                     # Revision number
        }
        device = driver_device.DriverDevice()
        device.vendor = pci_dict["vendor_id"]
        device.model = pci_dict.get('model', 'miss model info')
        std_board_info = {'device_id': pci_dict.get('device_id', None),
                          'class': pci_dict.get('class', None)}
        device.std_board_info = jsonutils.dumps(std_board_info)
        device.vendor_board_info = 'fake_vendor_info'
        device.type = orc.PGPU
        device.controlpath_id = self._generate_controlpath_id(pci_dict)
        device.deployable_list = self._generate_dep_list(pci_dict)
        npu_list.append(device)
        return npu_list

    def update(self, control_path, image_path):
        return True

    def get_stats(self):
        return {}
