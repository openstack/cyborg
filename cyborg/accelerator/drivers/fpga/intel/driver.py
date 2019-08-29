# Copyright 2018 Intel, Inc.
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
Cyborg Intel FPGA driver implementation.
"""

import subprocess

from oslo_log import log as logging

from cyborg.accelerator.drivers.fpga.base import FPGADriver
from cyborg.accelerator.drivers.fpga.intel import sysinfo
from cyborg.common import exception

LOG = logging.getLogger(__name__)


class IntelFPGADriver(FPGADriver):
    """Base class for FPGA drivers.

       This is just a virtual FPGA drivers interface.
       Vedor should implement their specific drivers.
    """
    VENDOR = "intel"

    def __init__(self, *args, **kwargs):
        pass

    def discover(self):
        return sysinfo.fpga_tree()

    def program(self, device_path, image):
        bdf = ""
        path = sysinfo.find_pf_by_vf(device_path) if sysinfo.is_vf(
            device_path) else device_path
        if sysinfo.is_bdf(device_path):
            bdf = sysinfo.get_pf_bdf(device_path)
        else:
            bdf = sysinfo.get_bdf_by_path(path)
        bdfs = sysinfo.split_bdf(bdf)
        cmd = ["sudo", "/usr/bin/fpgaconf"]
        for i in zip(["--bus", "--device", "--function"], bdfs):
            cmd.extend(i)
        cmd.append(image)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        p.wait()
        return p.returncode

    def program_v2(self, controlpath_id, image_file_path):
        """Program the FPGA with the provided bitstream image.

           TODO(Sundar): Need to handle retries.

           :param: controlpath_id
               Controlpath_id OVO
           :param: image_file_path
               String with the file path
           :returns: True on success, False on failure
        """
        if controlpath_id['cpid_type'] != "PCI":
            raise exception.InvalidType(obj='controlpath_id',
                                        type=controlpath_id['cpid_type'],
                                        expected='PCI')
        # TODO(Sundar) Do not hardcode fpgaconf. Use right tool based on
        #    bitstream type. New OPAE version with secure updates will
        #    unify more bitstream types.
        cmd = ["sudo", "/usr/bin/fpgaconf"]
        """
        # TODO() Should driver do this or the agent?
        controlpath_id['cpid_info'] = jsonutils.loads(
            controlpath_id['cpid_info'])
        """
        bdf_dict = controlpath_id['cpid_info']
        bdf = map(lambda x: bdf_dict[x], ["bus", "device", "function"])
        for i in zip(["--bus", "--device", "--function"], bdf):
            cmd.extend(i)
        cmd.append(image_file_path)
        LOG.info('Running command: %s', cmd)
        try:
            # TODO() Use oslo.privsep, not subprocess.Popen
            subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                    shell=False)
            return True
        except subprocess.CalledProcessError as e:
            LOG.error('Programming failed. Command: (%s) '
                      'Exception: (%s)', cmd, str(e))
            # TODO() if retryable error, try again
            return False
