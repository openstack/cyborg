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

from oslo_serialization import jsonutils

from cyborg.accelerator.common import utils
from cyborg.accelerator.drivers.driver import GenericDriver
from cyborg.common import constants
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device


class AscendDriver(GenericDriver):
    """The class for Ascend AI Chip drivers.

    This is the Huawei Ascend AI Chip drivers.
    """

    VENDOR = "huawei"

    # TODO(yikun): can be extracted into PCIDeviceDriver
    def _generate_controlpath_id(self, pci):
        driver_cpid = driver_controlpath_id.DriverControlPathID()
        driver_cpid.cpid_type = "PCI"
        driver_cpid.cpid_info = pci["slot_json"]
        return driver_cpid

    # TODO(yikun): can be extracted into PCIDeviceDriver
    def _generate_attach_handle(self, pci):
        driver_ah = driver_attach_handle.DriverAttachHandle()
        driver_ah.attach_type = "PCI"
        driver_ah.in_use = False
        driver_ah.attach_info = pci["slot_json"]
        return driver_ah

    # TODO(yikun): can be extracted into PCIDeviceDriver
    def _generate_dep_list(self, pci):
        driver_dep = driver_deployable.DriverDeployable()
        driver_dep.attach_handle_list = [self._generate_attach_handle(pci)]
        pci_addr_name = pci["address"].replace(":", "_").replace(".", "_")
        driver_dep.name = pci.get('device_name', '') + '_' + pci_addr_name
        driver_dep.num_accelerators = 1
        driver_dep.driver_name = self.VENDOR
        return [driver_dep]

    def discover(self):
        """The PCI line would be matched as:

        0000:0c:00.0 Processing acc [1200]: Device [19e5:d100] (rev 20)

        {
          'address': '0000:0c:00.0',           # domain:bus:device.function
          'device_name': 'Device',             # Name of the device
          'vendor_id': '19e5',                 # ID of the vendor
          'class_name': 'Processing accelerators',  # Name of the class
          'device_id': 'd100',                 # ID of the device
          'revision': '20'                     # Revision number
        }
        """
        ascends = (
            dev
            for dev in utils.get_pci_devices()
            if dev["device_id"] == "d100"
        )
        npu_list = []
        for ascend in ascends:
            ascend["slot_json"] = utils.pci_str_to_json(ascend["address"])
            device = driver_device.DriverDevice()
            device.stub = False
            device.vendor = ascend["vendor_id"]
            device.model = ascend.get('device_name', '')
            std_board_info = {
                'device_id': ascend.get('device_id', None),
                'class': ascend.get('class_name', None),
            }
            device.std_board_info = jsonutils.dumps(std_board_info)
            device.vendor_board_info = ''
            device.type = constants.DEVICE_AICHIP
            device.controlpath_id = self._generate_controlpath_id(ascend)
            device.deployable_list = self._generate_dep_list(ascend)
            npu_list.append(device)
        return npu_list

    def update(self, control_path, image_path):
        # TODO(yikun): To be implemented in future
        return True

    def get_stats(self):
        # TODO(yikun): To be implemented in future
        return {}
