#!/usr/bin/python
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

import argparse
import copy
import glob
import os
import shutil


PF0_ADDR = "0000:5e:00.0"
PF1_ADDR = "0000:be:00.0"
VF0_ADDR = "0000:5e:00.1"
FPGA_TREE = {
    "dev.0": {"bdf": PF0_ADDR,
              "regions": {"dev.2": {"bdf": VF0_ADDR}}},
    "dev.1": {"bdf": PF1_ADDR}}

SYS_DEVICES = "sys/devices"
PCI_DEVICES_PATH = "sys/bus/pci/devices"
SYS_CLASS_FPGA = "sys/class/fpga"

DEV_PREFIX = "intel-fpga"

PGFA_DEVICE_COMMON_SUB_DIR = ["power"]

PGFA_DEVICE_COMMON_CONTENT = {
    "broken_parity_status": "0",
    "class": "0x120000",
    "config": "",
    "consistent_dma_mask_bits": "64",
    "d3cold_allowed": "1",
    "device": "0x09c4",
    "dma_mask_bits": "64",
    "driver_override": "(null)",
    "enable": "1",
    "irq": "16",
    "local_cpulist": "0-111",
    "local_cpus": "00000000,00000000,00000000,00000000,00000000,"
                  "00000000,00000000,00000000,00000000,00000000,"
                  "0000ffff,ffffffff,ffffffff,ffffffff",
    "modalias": "pci:v00008086d0000BCC0sv00000000sd00000000bc12sc00i00",
    "msi_bus": "",
    "numa_node": "-1",
    "resource": [
        "0x00000000c6000000 0x00000000c607ffff 0x000000000014220c",
        "0x0000000000000000 0x0000000000000000 0x0000000000000000",
        "0x00000000c6080000 0x00000000c60fffff 0x000000000014220c",
        "0x0000000000000000 0x0000000000000000 0x0000000000000000",
        "0x0000000000000000 0x0000000000000000 0x0000000000000000",
        "0x0000000000000000 0x0000000000000000 0x0000000000000000",
        "0x0000000000000000 0x0000000000000000 0x0000000000000000",
        "0x00000000c6100000 0x00000000c617ffff 0x000000000014220c",
        "0x0000000000000000 0x0000000000000000 0x0000000000000000",
        "0x0000000000000000 0x0000000000000000 0x0000000000000000",
        "0x0000000000000000 0x0000000000000000 0x0000000000000000",
        "0x0000000000000000 0x0000000000000000 0x0000000000000000",
        "0x0000000000000000 0x0000000000000000 0x0000000000000000"],
    "resource0": "",
    "resource0_wc": "",
    "subsystem_device": "0x0000",
    "subsystem_vendor": "0x0000",
    "uevent": [
        "DRIVER=intel-fpga-pci",
        "PCI_CLASS=120000",
        "PCI_ID=8086:BCC0",
        "PCI_SUBSYS_ID=0000:0000",
        "PCI_SLOT_NAME=0000:5e:00.0",
        "MODALIAS=pci:v00008086d0000BCC0sv00000000sd00000000bc12sc00i00"],
    "vendor": "0x8086"}

PGFA_DEVICES_SPECIAL_COMMON_CONTENT = {
    "dev.0": {
        "resource2": "",
        "resource2_wc": "",
        "sriov_numvfs": "1",
        "sriov_totalvfs": "1",
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
        "resource2_wc": "",
        "sriov_numvfs": "0",
        "sriov_totalvfs": "1",
        "uevent": [
            "DRIVER=intel-fpga-pci",
            "PCI_CLASS=120000",
            "PCI_ID=8086:BCC0",
            "PCI_SUBSYS_ID=0000:0000",
            "PCI_SLOT_NAME=0000:be:00.0",
            "MODALIAS=pci:v00008086d0000BCC0sv00000000sd00000000bc12sc00i00"],
    },
    "dev.2": {
        "d3cold_allowed": "0",
        "device": "0x09c4",
        "modalias": "pci:v00008086d0000BCC0sv00000000sd00000000bc12sc00i00",
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
            "DRIVER=intel-fpga-pci",
            "PCI_CLASS=120000",
            "PCI_ID=8086:BCC1",
            "PCI_SUBSYS_ID=0000:0000",
            "PCI_SLOT_NAME=0000:5e:00.1",
            "MODALIAS=pci:v00008086d0000BCC1sv00000000sd00000000bc12sc00i00"],
    }
}

PGFA_DEVICE_COMMON_SOFT_LINK = {
    "driver": "../../../bus/pci/drivers/intel-fpga-pci",
    "iommu": "../../virtual/iommu/dmar8",
    "iommu_group": "../../../kernel/iommu_groups/75",
    "subsystem": "../../../bus/pci"
}

PGFA_DEVICES_SPECIAL_SOFT_LINK = {
    "dev.0": {
        "firmware_node": "../../LNXSYSTM:00/device:00/PNP0A08:18/device:1d4",
    },
    "dev.1": {
        "firmware_node": "../../LNXSYSTM:00/device:00/PNP0A08:19/device:1d5",
        "iommu": "../../virtual/iommu/dmar4",
        "iommu_group": "../../../kernel/iommu_groups/76",
    },
    "dev.2": {
        "iommu": "../../virtual/iommu/dmar9",
        "iommu_group": "../../../kernel/iommu_groups/81",
    }
}
PGFA_DEVICES_SPECIAL_SOFT_LINK = {
    "dev.0": {
        "firmware_node": "../../LNXSYSTM:00/device:00/PNP0A08:18/device:1d4",
    },
    "dev.1": {
        "firmware_node": "../../LNXSYSTM:00/device:00/PNP0A08:19/device:1d5",
        "iommu": "../../virtual/iommu/dmar4",
        "iommu_group": "../../../kernel/iommu_groups/76",
    },
    "dev.2": {
        "iommu": "../../virtual/iommu/dmar9",
        "iommu_group": "../../../kernel/iommu_groups/81",
    }
}

PGFA_DEVICE_PF_SOFT_LINK = {
    "virtfn": lambda k, v: (k + str(int(v.rsplit(".", 1)[-1]) - 1),
                            "/".join(["..", v]))
}

PGFA_DEVICE_VF_SOFT_LINK = {
    "physfn": lambda k, v: (k, "/".join(["..", v]))
}


def gen_fpga_content(path, dev):
    content = copy.copy(PGFA_DEVICE_COMMON_CONTENT)
    content.update(PGFA_DEVICES_SPECIAL_COMMON_CONTENT[dev])
    for k, v in content.items():
        p = os.path.join(path, k)
        if not v:
            os.mknod(p)
        elif type(v) is str:
            with open(p, 'a') as f:
                f.write(v + "\n")
        elif type(v) is list:
            with open(p, 'a') as f:
                f.writelines([item + "\n" for item in v])


def gen_fpga_sub_dir(path):
    for d in PGFA_DEVICE_COMMON_SUB_DIR:
        p = os.path.join(path, d)
        os.makedirs(p)


def gen_fpga_pf_soft_link(path, bdf):
    for k, v in PGFA_DEVICE_PF_SOFT_LINK.items():
        if callable(v):
            k, v = v(k, bdf)
        os.symlink(v, os.path.join(path, k))


def gen_fpga_common_soft_link(path, bdf):
    for k, v in PGFA_DEVICE_COMMON_SOFT_LINK.items():
        os.symlink(v, os.path.join(path, k))


def gen_fpga_vf_soft_link(path, bdf):
    for k, v in PGFA_DEVICE_VF_SOFT_LINK.items():
        if callable(v):
            k, v = v(k, bdf)
        os.symlink(v, os.path.join(path, k))


def create_devices_path_and_files(tree, device_path, class_fpga_path,
                                  vf=False, pfinfo=None):
    for k, v in tree.items():
        bdf = v["bdf"]
        pci_path = "pci" + bdf.rsplit(":", 1)[0]
        bdf_path = os.path.join(device_path, pci_path, bdf)
        ln = "-".join([DEV_PREFIX, k])
        dev_path = os.path.join(bdf_path, "fpga", ln)
        os.makedirs(dev_path)
        gen_fpga_content(bdf_path, k)
        gen_fpga_sub_dir(bdf_path)
        if vf:
            gen_fpga_pf_soft_link(pfinfo["path"], bdf)
            gen_fpga_vf_soft_link(bdf_path, pfinfo["bdf"])
        pfinfo = {"path": bdf_path, "bdf": bdf}
        if "regions" in v:
            create_devices_path_and_files(
                v["regions"], device_path, class_fpga_path, True, pfinfo)
        source = dev_path.split("sys")[-1]
        os.symlink("../.." + source, os.path.join(class_fpga_path, ln))
        os.symlink("../../../" + bdf, os.path.join(dev_path, "device"))
        pci_dev = os.path.join(device_path.split(SYS_DEVICES)[0],
                               PCI_DEVICES_PATH)
        if not os.path.exists(pci_dev):
            os.makedirs(pci_dev)
        os.symlink("../../.." + bdf_path.split("sys")[-1],
                   os.path.join(pci_dev, bdf))


def create_devices_soft_link(class_fpga_path):
    devs = glob.glob1(class_fpga_path, "*")
    for dev in devs:
        path = os.path.realpath("%s/%s/device" % (class_fpga_path, dev))
        softlinks = copy.copy(PGFA_DEVICE_COMMON_SOFT_LINK)
        softlinks.update(
            PGFA_DEVICES_SPECIAL_SOFT_LINK[dev.rsplit("-", 1)[-1]])
        for k, v in softlinks.items():
            source = os.path.normpath(os.path.join(path, v))
            if not os.path.exists(source):
                os.makedirs(source)
            os.symlink(v, os.path.join(path, k))


def create_fake_sysfs(prefix=""):
    sys_device = os.path.join(prefix, SYS_DEVICES)
    sys_class_fpga = os.path.join(prefix, SYS_CLASS_FPGA)
    basedir = os.path.dirname(sys_device)
    if os.path.exists(basedir):
        shutil.rmtree(basedir, ignore_errors=False, onerror=None)
    os.makedirs(sys_class_fpga)
    create_devices_path_and_files(FPGA_TREE, sys_device, sys_class_fpga)
    create_devices_soft_link(sys_class_fpga)


def main():
    create_fake_sysfs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a fake sysfs for intel FPGA.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("-p", "--prefix", type=str,
                        default="/tmp", dest="p",
                        help='Set the prefix path of the fake sysfs. '
                        'default "/tmp"')
    args = parser.parse_args()

    create_fake_sysfs(args.p)
