#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0
#
# Bounded QEMU/VFIO smoke test for ./fake_pci_sriov.ko.
#
# Purpose: prove that a fake VF can be created, rebound from the host loopback
# driver to pci_sim_vfio_pci, attached to QEMU with vfio-pci, and cleaned up.
# This is a host-side smoke test; it only verifies QEMU can start with the VF.
#
# Prerequisites: qemu-system-x86_64 or qemu-kvm, timeout, sudo without a password, vfio-pci,
# and a kernel that can load fake_pci_sriov.ko.
#
# Important environment variables:
# - MODULE: fake_pci_sriov module path, default ./fake_pci_sriov.ko
# - MODULE_ARGS: optional arguments passed to insmod
# - VFS: number of VFs to create on the first PF, default 1
# - QEMU_TIMEOUT/QEMU_KILL_AFTER: bounds for the QEMU run, defaults 12s/5s
# - QEMU_BIN: QEMU binary path, auto-detected when unset
# - ALLOW_UNSAFE_INTERRUPTS: set VFIO unsafe-interrupts knob when present,
#   default 1 for nested development environments
# - LOG: log file, default /tmp/fake_pci_qemu_vfio_smoke.log
#
# Exit status is zero when QEMU starts and exits within the bounded timeout.
# Example:
#   sudo -n true && bash pci-sim/run_fake_pci_qemu_vfio_smoke.sh

set -euo pipefail

MODULE=${MODULE:-./fake_pci_sriov.ko}
MODULE_ARGS=${MODULE_ARGS:-}
if [ -z "${QEMU_BIN:-}" ]; then
    if command -v qemu-system-x86_64 >/dev/null 2>&1; then
        QEMU_BIN=qemu-system-x86_64
    else
        QEMU_BIN=/usr/libexec/qemu-kvm
    fi
fi
VENDOR=${VENDOR:-0x1d55}
PF_DEVICE=${PF_DEVICE:-0x1000}
VF_DEVICE=${VF_DEVICE:-0x1001}
VFS=${VFS:-1}
QEMU_TIMEOUT=${QEMU_TIMEOUT:-12s}
QEMU_KILL_AFTER=${QEMU_KILL_AFTER:-5s}
ALLOW_UNSAFE_INTERRUPTS=${ALLOW_UNSAFE_INTERRUPTS:-1}
LOG=${LOG:-/tmp/fake_pci_qemu_vfio_smoke.log}

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

PF=""
VF=""
cleanup() {
    set +e
    msg "cleanup"
    if [ -n "${VF:-}" ] && [ -e "/sys/bus/pci/devices/$VF" ]; then
        if [ -e "/sys/bus/pci/devices/$VF/driver/unbind" ]; then
            echo "$VF" | sudo -n tee \
                "/sys/bus/pci/devices/$VF/driver/unbind" >/dev/null
        fi
        echo '' | sudo -n tee \
            "/sys/bus/pci/devices/$VF/driver_override" >/dev/null
    fi
    if [ -n "${PF:-}" ] && \
       [ -e "/sys/bus/pci/devices/$PF/sriov_numvfs" ]; then
        echo 0 | sudo -n tee "/sys/bus/pci/devices/$PF/sriov_numvfs" >/dev/null
    fi
    msg "log saved to $LOG"
}
trap cleanup EXIT

cd "$(dirname "$0")"

msg "preflight"
command -v "$QEMU_BIN"
command -v timeout
sudo -n true

if ! grep -q '^fake_pci_sriov ' /proc/modules; then
    msg "loading fake_pci_sriov $MODULE_ARGS"
    # shellcheck disable=SC2086
    sudo -n insmod "$MODULE" $MODULE_ARGS
else
    msg "fake_pci_sriov already loaded"
fi

PF=$(find_dev "$PF_DEVICE")
[ -n "$PF" ]
msg "PF=$PF"

msg "enable $VFS VF"
echo 0 | sudo -n tee "/sys/bus/pci/devices/$PF/sriov_numvfs" >/dev/null || true
echo "$VFS" | sudo -n tee "/sys/bus/pci/devices/$PF/sriov_numvfs" >/dev/null
sleep 1

VF=$(find_dev "$VF_DEVICE")
[ -n "$VF" ]
msg "VF=$VF"
readlink -f "/sys/bus/pci/devices/$VF/driver" || true

msg "bind VF to pci_sim_vfio_pci"
sudo -n modprobe vfio-pci
unsafe_int=/sys/module/vfio_iommu_type1/parameters/allow_unsafe_interrupts
if [ "$ALLOW_UNSAFE_INTERRUPTS" = 1 ] && [ -e "$unsafe_int" ]; then
    msg "enable vfio_iommu_type1.allow_unsafe_interrupts for nested test VM"
    echo Y | sudo -n tee "$unsafe_int" >/dev/null
fi
if [ -e "/sys/bus/pci/devices/$VF/driver/unbind" ]; then
    echo "$VF" | sudo -n tee \
        "/sys/bus/pci/devices/$VF/driver/unbind" >/dev/null
fi
echo pci_sim_vfio_pci | sudo -n tee \
    "/sys/bus/pci/devices/$VF/driver_override" >/dev/null
echo "$VF" | sudo -n tee /sys/bus/pci/drivers_probe >/dev/null
readlink -f "/sys/bus/pci/devices/$VF/driver"

msg "QEMU/VFIO smoke test; timeout rc=124 is expected"
set +e
sudo -n timeout --foreground --kill-after="$QEMU_KILL_AFTER" "$QEMU_TIMEOUT" \
    "$QEMU_BIN" \
        -nodefaults -display none -serial none -parallel none -monitor none \
        -machine q35,accel=kvm \
        -m 256M \
        -device vfio-pci,host="$VF" \
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
