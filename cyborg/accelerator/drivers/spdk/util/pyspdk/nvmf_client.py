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

from oslo_log import log as logging
from oslo_serialization import jsonutils

LOG = logging.getLogger(__name__)


class NvmfTgt(object):

    def __init__(self, py):
        super(NvmfTgt, self).__init__()
        self.py = py

    def get_rpc_methods(self):
        rpc_methods = self._get_json_objs(
            'get_rpc_methods', '10.0.2.15')
        return rpc_methods

    def get_bdevs(self):
        block_devices = self._get_json_objs(
            'get_bdevs', '10.0.2.15')
        return block_devices

    def delete_bdev(self, name):
        sub_args = [name]
        res = self.py.exec_rpc('delete_bdev', '10.0.2.15', sub_args=sub_args)
        LOG.info(res)

    def kill_instance(self, sig_name):
        sub_args = [sig_name]
        res = self.py.exec_rpc('kill_instance', '10.0.2.15', sub_args=sub_args)
        LOG.info(res)

    def construct_aio_bdev(self, filename, name, block_size):
        sub_args = [filename, name, str(block_size)]
        res = self.py.exec_rpc(
            'construct_aio_bdev',
            '10.0.2.15',
            sub_args=sub_args)
        LOG.info(res)

    def construct_error_bdev(self, basename):
        sub_args = [basename]
        res = self.py.exec_rpc(
            'construct_error_bdev',
            '10.0.2.15',
            sub_args=sub_args)
        LOG.info(res)

    def construct_nvme_bdev(
            self,
            name,
            trtype,
            traddr,
            adrfam=None,
            trsvcid=None,
            subnqn=None):
        sub_args = ["-b", "-t", "-a"]
        sub_args.insert(1, name)
        sub_args.insert(2, trtype)
        sub_args.insert(3, traddr)
        if adrfam is not None:
            sub_args.append("-f")
            sub_args.append(adrfam)
        if trsvcid is not None:
            sub_args.append("-s")
            sub_args.append(trsvcid)
        if subnqn is not None:
            sub_args.append("-n")
            sub_args.append(subnqn)
        res = self.py.exec_rpc(
            'construct_nvme_bdev',
            '10.0.2.15',
            sub_args=sub_args)
        return res

    def construct_null_bdev(self, name, total_size, block_size):
        sub_args = [name, str(total_size), str(block_size)]
        res = self.py.exec_rpc(
            'construct_null_bdev',
            '10.0.2.15',
            sub_args=sub_args)
        return res

    def construct_malloc_bdev(self, total_size, block_size):
        sub_args = [str(total_size), str(block_size)]
        res = self.py.exec_rpc(
            'construct_malloc_bdev',
            '10.0.2.15',
            sub_args=sub_args)
        LOG.info(res)

    def delete_nvmf_subsystem(self, nqn):
        sub_args = [nqn]
        res = self.py.exec_rpc(
            'delete_nvmf_subsystem',
            '10.0.2.15',
            sub_args=sub_args)
        LOG.info(res)

    def construct_nvmf_subsystem(
            self,
            nqn,
            listen,
            hosts,
            serial_number,
            namespaces):
        sub_args = [nqn, listen, hosts, serial_number, namespaces]
        res = self.py.exec_rpc(
            'construct_nvmf_subsystem',
            '10.0.2.15',
            sub_args=sub_args)
        LOG.info(res)

    def get_nvmf_subsystems(self):
        subsystems = self._get_json_objs(
            'get_nvmf_subsystems', '10.0.2.15')
        return subsystems

    def _get_json_objs(self, method, server_ip):
        res = self.py.exec_rpc(method, server_ip)
        json_obj = jsonutils.loads(res)
        return json_obj
