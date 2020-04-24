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

from oslo_concurrency import processutils
from oslo_serialization import jsonutils

import re

from cyborg.accelerator.common import utils
from cyborg.accelerator.drivers.driver import GenericDriver
from cyborg.common import constants
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device
import cyborg.privsep

PCI_INFO_PATTERN = re.compile(r"(?P<slot>[0-9a-f]{4}:[0-9a-f]{2}:"
                              r"[0-9a-f]{2}\.[0-9a-f]) "
                              r"(?P<class>.*) [\[].*]: (?P<device>.*) .*"
                              r"[\[](?P<vendor_id>[0-9a-fA-F]"
                              r"{4}):(?P<device_id>[0-9a-fA-F]{4})].*"
                              r"[(rev ](?P<revision>[0-9a-f]{2})")


@cyborg.privsep.sys_admin_pctxt.entrypoint
def lspci_privileged():
    cmd = ['lspci', '-nnn', '-D']
    return processutils.execute(*cmd)


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
        pci_addr_name = pci["slot"].replace(":", "_").replace(".", "_")
        driver_dep.name = pci.get('device', '') + '_' + pci_addr_name
        driver_dep.num_accelerators = 1
        driver_dep.driver_name = self.VENDOR
        return [driver_dep]

    # TODO(yikun): can be extracted into PCIDeviceDriver
    def _get_pci_lines(self, keywords=()):
        pci_lines = []
        if keywords:
            lspci_out = lspci_privileged()[0].split('\n')
            for i in range(len(lspci_out)):
                # filter out pci devices info that contains all keywords
                if all([k in (lspci_out[i]) for k in keywords]):
                    pci_lines.append(lspci_out[i])
        return pci_lines

    def discover(self):
        """The PCI line would be matched as:

        0000:0c:00.0 Processing acc [1200]: Device [19e5:d100] (rev 20)

        {
          'slot': '0000:0c:00.0',              # domain:bus:device.function
          'device': 'Device',                  # Name of the device
          'vendor_id': '19e5',                 # ID of the vendor
          'class': 'Processing accelerators',  # Name of the class
          'device_id': 'd100',                 # ID of the device
          'revision': '20'                     # Revision number
        }
        """
        ascends = self._get_pci_lines(('d100',))
        npu_list = []
        for ascend in ascends:
            m = PCI_INFO_PATTERN.match(ascend)
            if m:
                pci_dict = m.groupdict()
                pci_dict["slot_json"] = utils.pci_str_to_json(pci_dict["slot"])
                device = driver_device.DriverDevice()
                device.stub = False
                device.vendor = pci_dict["vendor_id"]
                device.model = pci_dict.get('model', '')
                std_board_info = {'device_id': pci_dict.get('device_id', None),
                                  'class': pci_dict.get('class', None)}
                device.std_board_info = jsonutils.dumps(std_board_info)
                device.vendor_board_info = ''
                device.type = constants.DEVICE_AICHIP
                device.controlpath_id = self._generate_controlpath_id(pci_dict)
                device.deployable_list = self._generate_dep_list(pci_dict)
                npu_list.append(device)
        return npu_list

    def update(self, control_path, image_path):
        # TODO(yikun): To be implemented in future
        return True

    def get_stats(self):
        # TODO(yikun): To be implemented in future
        return {}
