# Copyright 2021 Inspur, Inc.
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
Cyborg Xilinx FPGA driver implementation.
"""
from oslo_concurrency import processutils

from cyborg.accelerator.drivers.fpga.base import FPGADriver
from cyborg.accelerator.drivers.fpga.xilinx import sysinfo
from cyborg.common import exception
import cyborg.privsep


@cyborg.privsep.sys_admin_pctxt.entrypoint
def _fpga_program_privileged(cmd_args):
    # Example: xbmgmt program --device 0000:d8:00.0
    # --base --image xilinx-u250-gen3x16-base
    cmd = ["/opt/xilinx/xrt/bin/xbmgmt"]
    cmd.extend(cmd_args)
    return processutils.execute(*cmd)


class XilinxFPGADriver(FPGADriver):
    """Class for Xilinx FPGA drivers.
       Vendor should implement their specific drivers in this class.
    """
    VENDOR = "xilinx"

    def __init__(self, *args, **kwargs):
        pass

    def discover(self):
        return sysinfo.fpga_tree()

    def program(self, controlpath_id, image_file_path):
        """Program the FPGA with the provided bitstream image.

        :param controlpath_id: the ID of controlpath.
        :param image_file_path: the path of the image file
        :returns: True on success, False on failure
        """
        if controlpath_id['cpid_type'] != "PCI":
            raise exception.InvalidType(obj='controlpath_id',
                                        type=controlpath_id['cpid_type'],
                                        expected='PCI')
        cmd_args = ['program']
        cmd_args.append('--device')
        bdf_dict = controlpath_id['cpid_info']
        # BDF format: domain:bus:device:function
        bdf = ':'.join([s for s in map(lambda x: bdf_dict[x],
                        ['domain', 'bus', 'device', 'function'])])
        cmd_args.append(bdf)
        cmd_args.append('--base')
        cmd_args.append('--image')
        cmd_args.append(image_file_path)

        try:
            _fpga_program_privileged(cmd_args)
            return True
        except Exception:
            return False
