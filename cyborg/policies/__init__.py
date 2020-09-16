# Copyright 2020 ZTE Corporation.
# All Rights Reserved.
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


import itertools

from cyborg.common import policy as old_policy
from cyborg.policies import base
from cyborg.policies import device_profiles


def list_policies():
    return itertools.chain(
        base.list_policies(),
        device_profiles.list_policies(),
        # NOTE(yumeng)old_policies will also be loaded before they are replaced
        # by new policies
        old_policy.device_policies,
        old_policy.deployable_policies,
        old_policy.accelerator_request_policies,
        old_policy.fpga_policies,
    )
