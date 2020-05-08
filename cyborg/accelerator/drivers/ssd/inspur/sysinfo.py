# Copyright 2020 Inspur Electronic Information Industry Co.,LTD.
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
Cyborg Inspur NVMe SSD driver implementation.
"""

from cyborg.accelerator.drivers.ssd import utils

VENDOR_ID = '1bd4'


def nvme_ssd_tree():
    devs = utils.discover_ssds(VENDOR_ID)
    return devs
