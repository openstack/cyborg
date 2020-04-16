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

import os
import psutil
import re
import subprocess

from oslo_concurrency import processutils
from oslo_log import log as logging

import cyborg.privsep

LOG = logging.getLogger(__name__)


class PySPDK(object):

    def __init__(self, pname):
        super(PySPDK, self).__init__()
        self.pid = None
        self.pname = pname

    @cyborg.privsep.sys_admin_pctxt.entrypoint
    def start_server(self, spdk_dir, server_name):
        if not self.is_alive():
            self.init_hugepages(spdk_dir)
            server_dir = os.path.join(spdk_dir, 'app/')
            file_dir = self._search_file(server_dir, server_name)
            LOG.info(file_dir)
            os.chdir(file_dir)
            cmd = ['bash', server_name]
            out, err = processutils.execute(*cmd)
            return out

    @cyborg.privsep.sys_admin_pctxt.entrypoint
    def init_hugepages(self, spdk_dir):
        huge_dir = os.path.join(spdk_dir, 'scripts/')
        file_dir = self._search_file(huge_dir, 'setup.sh')
        LOG.info(file_dir)
        os.chdir(file_dir)
        cmd = ['bash', 'setup.sh']
        out, err = processutils.execute(*cmd)
        return out

    @staticmethod
    def _search_file(spdk_dir, file_name):
        for dirpath, dirnames, filenames in os.walk(spdk_dir):
            for filename in filenames:
                if filename == file_name:
                    return dirpath

    def _get_process_id(self):
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['pid', 'cmdline'])
                if re.search(self.pname, str(pinfo.get('cmdline'))):
                    self.pid = pinfo.get('pid')
                    return self.pid
            except psutil.NoSuchProcess:
                LOG.info("NoSuchProcess:%(pname)s", {"pname": self.pname})
        LOG.info("NoSuchProcess:%(pname)s", {"pname": self.pname})
        return self.pid

    def is_alive(self):
        self.pid = self._get_process_id()
        if self.pid:
            p = psutil.Process(self.pid)
            if p.is_running():
                return True
        return False

    @staticmethod
    def exec_rpc(method, server='127.0.0.1', port=5260, sub_args=None):
        exec_cmd = ["./rpc.py", "-s", "-p"]
        exec_cmd.insert(2, server)
        exec_cmd.insert(4, str(port))
        exec_cmd.insert(5, method)
        if sub_args is None:
            sub_args = []
        exec_cmd.extend(sub_args)
        p = subprocess.Popen(
            exec_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = p.communicate()
        return out
