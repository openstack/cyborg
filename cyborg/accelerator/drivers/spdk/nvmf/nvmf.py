"""
SPDK NVMFDRIVER module implementation.
"""

from cyborg.accelerator.drivers.spdk.util.pyspdk.nvmf_client import NvmfTgt
from oslo_log import log as logging
from cyborg.accelerator.common import exception
from cyborg.accelerator.drivers.spdk.util import common_fun
from cyborg.accelerator.drivers.spdk.spdk import SPDKDRIVER
from cyborg.accelerator.drivers.spdk.util.pyspdk.py_spdk import PySPDK

LOG = logging.getLogger(__name__)


class NVMFDRIVER(SPDKDRIVER):
    """NVMFDRIVER class.

    nvmf_tgt server app should be able to implement this driver.
    """

    SERVER = 'nvmf'

    def __init__(self, *args, **kwargs):
        super(NVMFDRIVER, self).__init__(*args, **kwargs)
        self.servers = common_fun.discover_servers()
        self.py = common_fun.get_py_client(self.SERVER)

    def discover_accelerator(self):
        if common_fun.check_for_setup_error(self.py, self.SERVER):
            return self.get_one_accelerator()

    def get_one_accelerator(self):
        acc_client = NvmfTgt(self.py)
        bdevs = acc_client.get_bdevs()
        # Display current blockdev list
        subsystems = acc_client.get_nvmf_subsystems()
        # Display nvmf subsystems
        accelerator_obj = {
            'server': self.SERVER,
            'bdevs': bdevs,
            'subsystems': subsystems
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

    def delete_subsystem(self, nqn):
        """Delete a nvmf subsystem

        :param nqn: Target nqn(ASCII).
        :raise exception: Invaid
        """
        if nqn == "":
            acc_client = NvmfTgt(self.py)
            acc_client.delete_nvmf_subsystem(nqn)
        else:
            raise exception.Invalid('Delete nvmf subsystem failed.')

    def construct_subsystem(self,
                            nqn,
                            listen,
                            hosts,
                            serial_number,
                            namespaces
                            ):
        """Add a nvmf subsystem

        :param nqn: Target nqn(ASCII).
        :param listen: comma-separated list of Listen
        <trtype:transport_name traddr:address trsvcid:port_id>
        pairs enclosed in quotes.  Format:'trtype:transport0
        traddr:traddr0 trsvcid:trsvcid0,trtype:transport1
        traddr:traddr1 trsvcid:trsvcid1' etc.
        Example: 'trtype:RDMA traddr:192.168.100.8 trsvcid:4420,
        trtype:RDMA traddr:192.168.100.9 trsvcid:4420.'
        :param hosts: Whitespace-separated list of host nqn list.
        :param serial_number: Example: 'SPDK00000000000001.
        :param namespaces: Whitespace-separated list of namespaces.
        :raise exception: Invaid
        """
        if ((namespaces != '' and listen != '') and
                (hosts != '' and serial_number != '')) and nqn != '':
            acc_client = NvmfTgt(self.py)
            acc_client.construct_nvmf_subsystem(nqn,
                                                listen,
                                                hosts,
                                                serial_number,
                                                namespaces
                                                )
        else:
            raise exception.Invalid('Construct nvmf subsystem failed.')
