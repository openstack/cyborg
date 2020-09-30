#!/usr/bin/python
# Copyright 2021 Intel, Inc.
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

import copy
import os
import shutil


PF0_ADDR = "0000:05:00.0"
PF1_ADDR = "0000:06:00.0"
VF0_ADDR = "0000:05:01.0"
NIC_TREE = {
    "dev.0": {"bdf": PF0_ADDR,
              "vfs": {"dev.2": {"bdf": VF0_ADDR}}},
    "dev.1": {"bdf": PF1_ADDR}}

SYS_DEVICES = "sys/devices"
PCI_DEVICES_PATH = "sys/bus/pci/devices"

DEV_PREFIX = "intel-nic"

NIC_DEVICE_COMMON_SUB_DIR = ["power", "msi_irqs"]

NIC_DEVICE_COMMON_CONTENT = {
    "broken_parity_status": "0",
    "class": "0x0b4000",
    "config": "",
    "consistent_dma_mask_bits": "64",
    "d3cold_allowed": "1",
    "device": "0x158b",
    "dma_mask_bits": "64",
    "driver_override": "(null)",
    "enable": "1",
    "irq": "33",
    "local_cpulist": "0-7,16-23",
    "local_cpus": "000000,00000000,00000000,00000000,00ff00ff",
    "max_link_speed": "5 GT/s",
    "max_link_width": "16",
    "modalias": "pci:v00008086d000037C8sv00008086sd00000002bc0Bsc40i00",
    "msi_bus": "1",
    "numa_node": "0",
    "resource0": "",
    "subsystem_device": "0x0002",
    "subsystem_vendor": "0x8086",
    "vendor": "0x8086"}

NIC_DEVICES_SPECIAL_COMMON_CONTENT = {
    "dev.0": {
        "resource": [
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x00000000d1340000 0x00000000d137ffff 0x0000000000140204",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x00000000d1300000 0x00000000d133ffff 0x0000000000140204",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x00000000d1390000 0x00000000d139ffff 0x0000000000140204",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x00000000d1390000 0x00000000d139ffff 0x0000000000140204",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000"],
        "resource2": "",
        "resource4": "",
        "sriov_numvfs": "1",
        "sriov_totalvfs": "1",
        "uevent": [
            "DRIVER=c6xx",
            "PCI_CLASS=B4000",
            "PCI_ID=8086:37C8",
            "PCI_SUBSYS_ID=8086:0002",
            "PCI_SLOT_NAME=0000:05:00.0",
            "MODALIAS=pci:v00008086d000037C8sv00008086sd00000002bc0Bsc40i00"],
    },
    "dev.1": {
        "resource": [
            "0x00000000fbc00000 0x00000000fbc7ffff 0x000000000014220c",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x00000000fbc80000 0x00000000fbcfffff 0x000000000014220c",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x00000000fbd00000 0x00000000fbd7ffff 0x000000000014220c",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000"],
        "resource2": "",
        "sriov_numvfs": "0",
        "sriov_totalvfs": "0",
        "uevent": [
            "DRIVER=c6xx",
            "PCI_CLASS=B4000",
            "PCI_ID=8086:37C8",
            "PCI_SUBSYS_ID=8086:0002",
            "PCI_SLOT_NAME=0000:06:00.0",
            "MODALIAS=pci:v00008086d000037C8sv00008086sd00000002bc0Bsc40i00"],
    },
    "dev.2": {
        "d3cold_allowed": "0",
        "device": "0x37c9",
        "modalias": "pci:v00008086d000037C9sv00008086sd00000000bc0Bsc40i00",
        "irq": "0",
        "resource": [
            "0x00000000c6100000 0x00000000c617ffff 0x000000000014220c",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000",
            "0x0000000000000000 0x0000000000000000 0x0000000000000000"],
        "uevent": [
            "DRIVER=c6xx",
            "PCI_CLASS=B4000",
            "PCI_ID=8086:37C8",
            "PCI_SUBSYS_ID=8086:0002",
            "PCI_SLOT_NAME=0000:05:01.0",
            "MODALIAS=pci:v00008086d000037C8sv00008086sd00000002bc0Bsc40i00"],
    }
}

NIC_DEVICE_COMMON_SOFT_LINK = {
    "driver": "../../../../../../bus/pci/drivers/c6xx",
    "iommu": "../../../../../virtual/iommu/dmar1",
    "subsystem": "../../../../../../bus/pci"
}

NIC_DEVICES_SPECIAL_SOFT_LINK = {
    "dev.0": {
        "driver": "../../../../../..//bus/pci/drivers/c6xx",
        "iommu_group": "../../../../../../kernel/iommu_groups/20",
        # "virtfn0": "../0000:05:01.0/",
    },
    "dev.1": {
        "driver": "../../../../../..//bus/pci/drivers/c6xx",
        "iommu_group": "../../../../../../kernel/iommu_groups/21",
    },
    "dev.2": {
        "iommu_group": "../../../../../../kernel/iommu_groups/67",
        # "physfn": "../0000:05:00.0/",
    }
}

NIC_DEVICE_PF_SOFT_LINK = {
    "virtfn": lambda k, v: (k + str(int(v.rsplit(".", 1)[-1])),
                            "/".join(["..", v]))
}

NIC_DEVICE_VF_SOFT_LINK = {
    "physfn": lambda k, v: (k, "/".join(["..", v]))
}


def gen_nic_content(path, dev):
    content = copy.copy(NIC_DEVICE_COMMON_CONTENT)
    content.update(NIC_DEVICES_SPECIAL_COMMON_CONTENT[dev])
    for k, v in content.items():
        p = os.path.join(path, k)
        if not v:
            os.mknod(p)
        elif type(v) is str:
            with open(p, 'a') as f:
                f.write(v + "\n")
        elif type(v) is list:
            with open(p, 'a') as f:
                f.writelines([l + "\n" for l in v])


def gen_nic_sub_dir(path):
    for d in NIC_DEVICE_COMMON_SUB_DIR:
        p = os.path.join(path, d)
        os.makedirs(p)


def gen_nic_pf_soft_link(path, bdf):
    for k, v in NIC_DEVICE_PF_SOFT_LINK.items():
        if callable(v):
            k, v = v(k, bdf)
        os.symlink(v, os.path.join(path, k))


def gen_nic_common_soft_link(path, bdf):
    for k, v in NIC_DEVICE_COMMON_SOFT_LINK.items():
        os.symlink(v, os.path.join(path, k))


def gen_nic_vf_soft_link(path, bdf):
    for k, v in NIC_DEVICE_VF_SOFT_LINK.items():
        if callable(v):
            k, v = v(k, bdf)
        os.symlink(v, os.path.join(path, k))


def create_devices_path_and_files(tree, device_path, vf=False, pfinfo=None):
    for k, v in tree.items():
        bdf = v["bdf"]
        pci_path = "pci" + bdf.rsplit(":", 1)[0]
        bdf_path = os.path.join(device_path, pci_path, bdf)
        ln = "-".join([DEV_PREFIX, k])
        dev_path = os.path.join(bdf_path, "nic", ln)
        os.makedirs(dev_path)
        gen_nic_content(bdf_path, k)
        gen_nic_sub_dir(bdf_path)
        if vf:
            gen_nic_pf_soft_link(pfinfo["path"], bdf)
            gen_nic_vf_soft_link(bdf_path, pfinfo["bdf"])
        pfinfo = {"path": bdf_path, "bdf": bdf}
        if "vfs" in v:
            create_devices_path_and_files(
                v["vfs"], device_path, True, pfinfo)
        os.symlink("../../../" + bdf, os.path.join(dev_path, "device"))
        pci_dev = os.path.join(device_path.split(SYS_DEVICES)[0],
                               PCI_DEVICES_PATH)
        if not os.path.exists(pci_dev):
            os.makedirs(pci_dev)
        os.symlink("../../.." + bdf_path.split("sys")[-1],
                   os.path.join(pci_dev, bdf))


def create_fake_sysfs(prefix=""):
    sys_device = os.path.join(prefix, SYS_DEVICES)
    basedir = os.path.dirname(sys_device)
    if os.path.exists(basedir):
        shutil.rmtree(basedir, ignore_errors=False, onerror=None)
    create_devices_path_and_files(NIC_TREE, sys_device)
