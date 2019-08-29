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

"""
SPDK VHOSTDRIVER module implementation.
"""

from oslo_log import log as logging

from cyborg.accelerator.drivers.spdk.spdk import SPDKDRIVER
from cyborg.accelerator.drivers.spdk.util import common_fun
from cyborg.accelerator.drivers.spdk.util.pyspdk.py_spdk import PySPDK
from cyborg.accelerator.drivers.spdk.util.pyspdk.vhost_client import VhostTgt

LOG = logging.getLogger(__name__)


class VHOSTDRIVER(SPDKDRIVER):
    """VHOSTDRIVER class.

       vhost server app should be able to implement this driver.
    """

    SERVER = 'vhost'

    def __init__(self, *args, **kwargs):
        super(VHOSTDRIVER, self).__init__(*args, **kwargs)
        self.servers = common_fun.discover_servers()
        self.py = common_fun.get_py_client(self.SERVER)

    def discover_accelerator(self):
        if common_fun.check_for_setup_error(self.py, self.SERVER):
            return self.get_one_accelerator()

    def get_one_accelerator(self):
        acc_client = VhostTgt(self.py)
        bdevs = acc_client.get_bdevs()
        # Display current blockdev list
        scsi_devices = acc_client.get_scsi_devices()
        # Display SCSI devices
        luns = acc_client.get_luns()
        # Display active LUNs
        interfaces = acc_client.get_interfaces()
        # Display current interface list
        accelerator_obj = {
            'server': self.SERVER,
            'bdevs': bdevs,
            'scsi_devices': scsi_devices,
            'luns': luns,
            'interfaces': interfaces
        }
        return accelerator_obj

    def install_accelerator(self, driver_id, driver_type):
        pass

    def uninstall_accelerator(self, driver_id, driver_type):
        pass

    def accelerator_list(self):
        return self.get_all_accelerators()

    def get_all_accelerators(self):
        accelerators = []
        for accelerator_i in range(len(self.servers)):
            accelerator = self.servers[accelerator_i]
            py_tmp = PySPDK(accelerator)
            if py_tmp.is_alive():
                accelerators.append(self.get_one_accelerator())
        return accelerators

    def update(self, driver_type, **kwargs):
        pass

    def attach_instance(self, instance_id):
        pass

    def detach_instance(self, instance_id):
        pass

    def add_ip_address(self, ifc_index, ip_addr):
        """Add IP address

        :param ifc_index: ifc index of the nic device.
        :param ip_addr: ip address will be added.
        :return: ip_address
        """
        acc_client = VhostTgt(self.py)
        return acc_client.add_ip_address(ifc_index, ip_addr)

    def delete_ip_address(self, ifc_index, ip_addr):
        """Delete IP address

        :param ifc_index: ifc index of the nic device.
        :param ip_addr: ip address will be added.
        :return: ip_address
        """
        acc_client = VhostTgt(self.py)
        return acc_client.delete_ip_address(ifc_index, ip_addr)
