#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0
#
# Bounded QEMU/VFIO smoke test for mdev (mediated device) passthrough.
#
# Purpose: prove that a fake mdev instance can be created from the pci-sim
# module, attached to QEMU with vfio-pci via sysfsdev, and cleaned up.
# This is a host-side smoke test; it only verifies QEMU can start with the
# mdev device.
#
# Prerequisites: qemu-system-x86_64 or qemu-kvm, timeout, sudo without a
# password, vfio-pci and the kernel mdev framework (CONFIG_VFIO_MDEV), and
# a kernel that can load fake_pci_sriov.ko.
#
# Important environment variables:
# - MODULE: fake_pci_sriov module path, default ./fake_pci_sriov.ko
# - MODULE_ARGS: arguments passed to insmod, default "mdev_instances=8"
# - VENDOR/PF_DEVICE: PCI IDs for the fake PF, defaults 0x1d55/0x1000
# - MDEV_TYPE: mdev type suffix to use, default "sim_accel_small"
# - QEMU_TIMEOUT/QEMU_KILL_AFTER: bounds for the QEMU run, defaults 12s/5s
# - QEMU_BIN: QEMU binary path, auto-detected when unset
# - ALLOW_UNSAFE_INTERRUPTS: set VFIO unsafe-interrupts knob when present,
#   default 1 for nested development environments
# - LOG: log file, default /tmp/fake_pci_qemu_mdev_smoke.log
#
# Exit status is zero when QEMU starts and exits within the bounded timeout.
# Example:
#   sudo -n true && bash pci-sim/run_fake_pci_qemu_mdev_smoke.sh

set -euo pipefail

MODULE=${MODULE:-./fake_pci_sriov.ko}
MODULE_ARGS=${MODULE_ARGS:-"mdev_instances=8"}
if [ -z "${QEMU_BIN:-}" ]; then
    if command -v qemu-system-x86_64 >/dev/null 2>&1; then
        QEMU_BIN=qemu-system-x86_64
    else
        QEMU_BIN=/usr/libexec/qemu-kvm
    fi
fi
VENDOR=${VENDOR:-0x1d55}
PF_DEVICE=${PF_DEVICE:-0x1000}
MDEV_TYPE=${MDEV_TYPE:-sim_accel_small}
QEMU_TIMEOUT=${QEMU_TIMEOUT:-12s}
QEMU_KILL_AFTER=${QEMU_KILL_AFTER:-5s}
ALLOW_UNSAFE_INTERRUPTS=${ALLOW_UNSAFE_INTERRUPTS:-1}
LOG=${LOG:-/tmp/fake_pci_qemu_mdev_smoke.log}
UUID="deadbeef-dead-beef-dead-beefdeadbeef"

: > "$LOG"
exec > >(tee -a "$LOG") 2>&1

msg() { echo "== $* =="; }
find_dev() {
    local device=$1
    local d
    for d in /sys/bus/pci/devices/*; do
        [ "$(cat "$d/vendor" 2>/dev/null || true)" = "$VENDOR" ] || continue
        [ "$(cat "$d/device" 2>/dev/null || true)" = "$device" ] || continue
        basename "$d"
        return 0
    done
    return 1
}

cleanup() {
    set +e
    msg "cleanup"
    if [ -d "/sys/bus/mdev/devices/$UUID" ]; then
        echo 1 | sudo -n tee "/sys/bus/mdev/devices/$UUID/remove" >/dev/null
    fi
    msg "log saved to $LOG"
}
trap cleanup EXIT

# Resolve MODULE relative to the invocation directory before the cd below,
# so 'MODULE=./pci-sim/fake_pci_sriov.ko
# pci-sim/run_fake_pci_qemu_mdev_smoke.sh' works from the repository root.
INVOKED_FROM=$PWD
cd "$(dirname "$0")"
case $MODULE in
    /*) ;;
    *) MODULE=$INVOKED_FROM/$MODULE ;;
esac

msg "preflight"
command -v "$QEMU_BIN"
command -v timeout
sudo -n true

if ! grep -q '^fake_pci_sriov ' /proc/modules; then
    msg "loading mdev + fake_pci_sriov $MODULE_ARGS"
    sudo -n modprobe mdev
    # shellcheck disable=SC2086
    sudo -n insmod "$MODULE" $MODULE_ARGS
else
    msg "fake_pci_sriov already loaded"
fi

PF=$(find_dev "$PF_DEVICE")
[ -n "$PF" ]
msg "PF=$PF"

msg "set vf_personality to mdev"
echo mdev | sudo -n tee \
    "/sys/bus/pci/devices/$PF/vf_personality" >/dev/null
sleep 1

MDEV_BUS="/sys/class/mdev_bus/$PF"
[ -d "$MDEV_BUS" ] || {
    echo "FAIL: $MDEV_BUS does not exist; is vf_personality set to mdev?"
    exit 1
}

msg "find mdev type matching *$MDEV_TYPE"
TYPES_DIR="$MDEV_BUS/mdev_supported_types"
TYPE_DIR=$(find "$TYPES_DIR" -maxdepth 1 -name "*$MDEV_TYPE" -type d | head -1)
[ -n "$TYPE_DIR" ] || {
    echo "FAIL: no mdev type matching *$MDEV_TYPE under $TYPES_DIR"
    ls -la "$TYPES_DIR"/
    exit 1
}
echo "TYPE_DIR=$TYPE_DIR"

msg "create mdev instance $UUID"
echo "$UUID" | sudo -n tee "$TYPE_DIR/create" > /dev/null
sleep 1

[ -d "/sys/bus/mdev/devices/$UUID" ] || {
    echo "FAIL: mdev instance $UUID not found on mdev bus"
    exit 1
}
echo "OK: mdev instance $UUID created"

if [ "$ALLOW_UNSAFE_INTERRUPTS" = 1 ] && \
   [ -e /sys/module/vfio_iommu_type1/parameters/allow_unsafe_interrupts ]; then
    msg "enable vfio_iommu_type1.allow_unsafe_interrupts for nested test VM"
    UNSAFE=/sys/module/vfio_iommu_type1/parameters/allow_unsafe_interrupts
    echo Y | sudo -n tee "$UNSAFE" >/dev/null
fi

msg "QEMU/mdev smoke test; timeout rc=124 is expected"
set +e
sudo -n timeout --foreground --kill-after="$QEMU_KILL_AFTER" "$QEMU_TIMEOUT" \
    "$QEMU_BIN" \
        -nodefaults -display none -serial none -parallel none -monitor none \
        -machine q35,accel=kvm \
        -m 256M \
        -device vfio-pci,sysfsdev=/sys/bus/mdev/devices/"$UUID" \
        -S
QEMU_RC=$?
set -e
echo "QEMU_RC=$QEMU_RC"

msg "recent kernel log"
sudo -n dmesg | tail -160

if [ "$QEMU_RC" -eq 124 ] || [ "$QEMU_RC" -eq 0 ]; then
    msg "PASS"
    exit 0
fi

msg "FAIL: unexpected QEMU rc $QEMU_RC"
exit "$QEMU_RC"
