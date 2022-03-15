# Copyright 2017 Huawei Technologies Co.,LTD.
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
import os_resource_classes as orc

CONDUCTOR_TOPIC = 'cyborg-conductor'
AGENT_TOPIC = 'cyborg-agent'
DEVICE_GPU = 'GPU'
DEVICE_FPGA = 'FPGA'
DEVICE_AICHIP = 'AICHIP'
DEVICE_QAT = 'QAT'
DEVICE_NIC = 'NIC'
DEVICE_SSD = 'SSD'


ARQ_STATES = (ARQ_INITIAL, ARQ_BIND_STARTED, ARQ_BOUND, ARQ_UNBOUND,
              ARQ_BIND_FAILED, ARQ_UNBIND_FAILED, ARQ_DELETING) = (
    'Initial', 'BindStarted', 'Bound', 'Unbound', 'BindFailed', 'UnbindFailed',
    'Deleting')


ARQ_BIND_STAGE = (ARQ_PRE_BIND, ARQ_FINISH_BIND,
                  ARQ_OUFOF_BIND_FLOW) = (
    [ARQ_INITIAL, ARQ_BIND_STARTED],
    [ARQ_BOUND, ARQ_BIND_FAILED],
    [ARQ_UNBOUND, ARQ_DELETING])


ARQ_BIND_STATUS = (ARQ_BIND_STATUS_FINISH, ARQ_BIND_STATUS_FAILED) = (
    "completed", "failed")


ARQ_BIND_STATES_STATUS_MAP = {
    ARQ_BOUND: ARQ_BIND_STATUS_FINISH,
    ARQ_BIND_FAILED: ARQ_BIND_STATUS_FAILED,
    ARQ_DELETING: ARQ_BIND_STATUS_FAILED
}

# TODO(Shaohe): maybe we can use oslo automaton lib
# ref: https://docs.openstack.org/automaton/latest/user/examples.html
# The states in value list can transfrom to the key state
ARQ_STATES_TRANSFORM_MATRIX = {
    ARQ_INITIAL: [],
    ARQ_BIND_STARTED: [ARQ_INITIAL, ARQ_UNBOUND],
    ARQ_BOUND: [ARQ_BIND_STARTED],
    ARQ_UNBOUND: [ARQ_INITIAL, ARQ_BIND_STARTED, ARQ_BOUND, ARQ_BIND_FAILED],
    ARQ_BIND_FAILED: [ARQ_BIND_STARTED, ARQ_BOUND],
    ARQ_DELETING: [ARQ_INITIAL, ARQ_BIND_STARTED, ARQ_BOUND,
                   ARQ_UNBOUND, ARQ_BIND_FAILED]
}


# Device type
DEVICE_TYPE = (DEVICE_GPU, DEVICE_FPGA, DEVICE_AICHIP, DEVICE_QAT, DEVICE_NIC,
               DEVICE_SSD)


# Attach handle type
#  'TEST_PCI': used by fake driver, ignored by Nova virt driver.
ATTACH_HANDLE_TYPES = (AH_TYPE_PCI, AH_TYPE_MDEV, AH_TYPE_TEST_PCI) = (
    "PCI", "MDEV", "TEST_PCI")


# Control Path ID type
CPID_TYPE = (CPID_TYPE_PCI) = ("PCI")


# Resource Class
RESOURCES = {
    "FPGA": orc.FPGA,
    "PGPU": orc.PGPU,
    "VGPU": orc.VGPU,
    "QAT": "CUSTOM_QAT",
    "NIC": "CUSTOM_NIC",
    "SSD": 'CUSTOM_SSD',
}


ACCEL_SPECS = (
    ACCEL_BITSTREAM_ID,
    ACCEL_FUNCTION_ID
) = (
    "accel:bitstream_id",
    "accel:function_id"
)


SUPPORT_RESOURCES = (
    FPGA, GPU, VGPU, PGPU, QAT, NIC, SSD) = (
    "FPGA", "GPU", "VGPU", "PGPU", "CUSTOM_QAT", "CUSTOM_NIC", "CUSTOM_SSD"
)


FPGA_TRAITS = (
    FPGA_FUNCTION_ID,
) = (
    "CUSTOM_FPGA_FUNCTION_ID",
)


RESOURCES_PREFIX = "resources:"
