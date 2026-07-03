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
PERL ?= perl
LINT_BASE ?= origin/master

PCI_SIM_FORMAT_FILES := $(wildcard $(PWD)/*.c) $(wildcard $(PWD)/*.h)
PCI_SIM_CHECKPATCH_PATHS := *.c *.h Kconfig Makefile *.rst

.PHONY: all modules clean install modules_install check check-kernel-config \
	lint lint-checkpatch lint-format lint-build-warnings test test-build \
	test-host test-loopback test-multi-pf

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

check: lint lint-build-warnings

lint:
	@status=0; \
	$(MAKE) lint-checkpatch || status=$$?; \
	$(MAKE) lint-format || status=$$?; \
	exit $$status

lint-checkpatch:
	git diff --no-ext-diff $(LINT_BASE) -- $(PCI_SIM_CHECKPATCH_PATHS) | \
		$(PERL) $(PWD)/tools/checkpatch.pl --no-signoff --strict \
		--show-types \
		--ignore OPEN_ENDED_LINE,CONSTANT_COMPARISON \
		--ignore LINUX_VERSION_CODE,EMBEDDED_FILENAME,FILE_PATH_CHANGES \
		--no-tree --no-spelling --patch -

lint-format:
	@if ! command -v git-clang-format >/dev/null 2>&1; then \
		echo "git-clang-format is required for incremental format checks"; \
		exit 1; \
	fi
	git clang-format --extensions c,h $(LINT_BASE) -- \
		$(PCI_SIM_FORMAT_FILES)
	@if ! git diff --quiet -- $(PCI_SIM_FORMAT_FILES); then \
		echo "git clang-format updated files; review and include them"; \
		git diff -- $(PCI_SIM_FORMAT_FILES); \
		exit 1; \
	fi

lint-build-warnings:
	$(MAKE) W=1 test-build
	$(MAKE) clean

# Non-privileged build validation for CI and local development.
test-build: modules

# Run host-side tests. Requires sudo and a kernel that supports module loading.
test: test-build test-host

test-host: test-loopback test-multi-pf

test-loopback:
	sudo -n python3 $(PWD)/test_pci_sim_loopback.py --reload --unload \
		--module $(PWD)/fake_pci_sriov.ko

test-multi-pf:
	bash $(PWD)/run_fake_pci_multi_pf_smoke.sh
