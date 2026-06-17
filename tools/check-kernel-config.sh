#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

KVER=${KVER:-$(uname -r)}
CONFIG=${CONFIG:-/boot/config-$KVER}

if [[ ! -r "$CONFIG" ]]; then
    echo "ERROR: cannot read $CONFIG" >&2
    exit 1
fi

require_y() {
    local opt=$1
    if ! grep -qx "${opt}=y" "$CONFIG"; then
        echo "ERROR: $opt must be built-in (=y) in $CONFIG" >&2
        return 1
    fi
}

require_enabled() {
    local opt=$1
    if ! grep -Eq "^${opt}=(y|m)$" "$CONFIG"; then
        echo "ERROR: $opt must be enabled (=y or =m) in $CONFIG" >&2
        return 1
    fi
}

warn_enabled() {
    local opt=$1
    if ! grep -Eq "^${opt}=(y|m)$" "$CONFIG"; then
        echo "WARNING: $opt is not enabled in $CONFIG" >&2
    fi
}

failed=0
require_y CONFIG_MODULES || failed=1
require_y CONFIG_PCI || failed=1
require_y CONFIG_PCI_DOMAINS || failed=1
require_y CONFIG_IOMMU_API || failed=1
require_y CONFIG_TTY || failed=1
require_enabled CONFIG_VFIO || failed=1
require_enabled CONFIG_VFIO_PCI_CORE || failed=1

# Runtime/test dependencies for the supplied smoke tests.
warn_enabled CONFIG_PCI_IOV
warn_enabled CONFIG_VFIO_PCI
warn_enabled CONFIG_KVM

if [[ $failed -ne 0 ]]; then
    exit 1
fi

echo "Kernel config dependencies look usable for pci-sim on $KVER"
