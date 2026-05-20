# SPDX-License-Identifier: GPL-2.0-only

obj-m += fake_pci_sriov.o
fake_pci_sriov-y := \
	fake_pci_sriov_core.o \
	fake_pci_sriov_cfg.o \
	fake_pci_sriov_iommu.o \
	fake_pci_sriov_uart.o \
	fake_pci_sriov_vfio.o

KDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(CURDIR)

.PHONY: all modules clean install modules_install check-kernel-config \
	test test-loopback test-multi-pf

all: modules

modules:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

install modules_install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a

check-kernel-config:
	../tools/check-kernel-config.sh

# Run host-side tests. Requires sudo and a kernel that supports module loading.
# Build the module first with 'make modules'.
test: test-loopback test-multi-pf

test-loopback:
	sudo -n python3 $(PWD)/test_pci_sim_loopback.py --reload --unload \
		--module $(PWD)/fake_pci_sriov.ko

test-multi-pf:
	bash $(PWD)/run_fake_pci_multi_pf_smoke.sh
