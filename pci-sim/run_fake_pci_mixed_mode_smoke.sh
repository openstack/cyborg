#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0
#
# Host-side smoke test for mixed SR-IOV and mdev PF modes.
#
# Purpose: load the module with two PFs, set the second PF's personality to
# mdev, verify that the uart PF supports VFs and has no mdev_bus entry, and
# that the mdev PF appears under /sys/class/mdev_bus/ and rejects
# sriov_numvfs writes.
#
# Prerequisites: sudo without a password, vfio-pci and the kernel mdev
# framework (CONFIG_VFIO_MDEV), and a kernel that can load
# fake_pci_sriov.ko.
#
# Exit status is zero when all checks pass and cleanup succeeds.
set -euo pipefail

MODULE=${MODULE:-./fake_pci_sriov.ko}
MODULE_ARGS=${MODULE_ARGS:-"num_pfs=2 mdev_instances=4"}
VENDOR=${VENDOR:-0x1d55}
PF_DEVICE=${PF_DEVICE:-0x1000}
VF_DEVICE=${VF_DEVICE:-0x1001}
LOG=${LOG:-/tmp/fake_pci_mixed_mode_smoke.log}

: >"$LOG"
exec > >(tee -a "$LOG") 2>&1

msg() { echo "== $* =="; }

find_fake_devs() {
    local device=$1 d
    for d in /sys/bus/pci/devices/*; do
        [ "$(cat "$d/vendor" 2>/dev/null || true)" = "$VENDOR" ] || continue
        [ "$(cat "$d/device" 2>/dev/null || true)" = "$device" ] || continue
        basename "$d"
    done | sort
}

assert_file_content() {
    local path=$1 expected=$2 actual
    actual=$(cat "$path" 2>/dev/null | tr -d '[:space:]')
    echo "CHECK $path = '$actual' (expect '$expected')"
    [ "$actual" = "$expected" ] || {
        echo "FAIL: $path content '$actual', expected '$expected'"
        exit 1
    }
}

cleanup() {
    set +e
    msg cleanup
    LOG=/tmp/fake_pci_mixed_mode_cleanup.log \
        ./cleanup_fake_pci_sriov.sh || true
    msg "log saved to $LOG"
}
trap cleanup EXIT

# Resolve MODULE relative to the invocation directory before the cd below,
# so 'MODULE=./pci-sim/fake_pci_sriov.ko
# pci-sim/run_fake_pci_mixed_mode_smoke.sh' works from the repository root.
INVOKED_FROM=$PWD
cd "$(dirname "$0")"
case $MODULE in
    /*) ;;
    *) MODULE=$INVOKED_FROM/$MODULE ;;
esac
sudo -n true

if grep -q '^fake_pci_sriov ' /proc/modules ||
    [ -n "$(find_fake_devs "$PF_DEVICE")" ]; then
    LOG=/tmp/fake_pci_mixed_mode_pre_cleanup.log \
        ./cleanup_fake_pci_sriov.sh || true
fi

msg "preload VFIO/mdev dependencies"
sudo -n modprobe mdev
sudo -n modprobe vfio-pci

msg "insmod $MODULE $MODULE_ARGS"
# shellcheck disable=SC2086
sudo -n insmod "$MODULE" $MODULE_ARGS
sleep 1

mapfile -t pfs < <(find_fake_devs "$PF_DEVICE")
printf 'PF_LIST=%s\n' "${pfs[*]}"
[ "${#pfs[@]}" -eq 2 ] || {
    echo "FAIL: expected 2 PFs, found ${#pfs[@]}"
    exit 1
}

SRIOV_PF="${pfs[0]}"
MDEV_PF="${pfs[1]}"
echo "SRIOV_PF=$SRIOV_PF  MDEV_PF=$MDEV_PF"

msg "set vf_personality on mdev PF"
echo mdev | sudo -n tee \
    "/sys/bus/pci/devices/$MDEV_PF/vf_personality" >/dev/null
sleep 1

# --- SR-IOV PF checks ---

msg "verify SR-IOV PF has no mdev_bus entry"
[ ! -d "/sys/class/mdev_bus/$SRIOV_PF" ] || {
    echo "FAIL: SR-IOV PF $SRIOV_PF has mdev_bus entry"
    exit 1
}
echo "OK: no mdev_bus entry for SR-IOV PF"

msg "enable VFs on SR-IOV PF"
echo 2 | sudo -n tee \
    "/sys/bus/pci/devices/$SRIOV_PF/sriov_numvfs" >/dev/null
sleep 1

mapfile -t vfs < <(find_fake_devs "$VF_DEVICE")
printf 'VF_LIST=%s\n' "${vfs[*]}"
[ "${#vfs[@]}" -eq 2 ] || {
    echo "FAIL: expected 2 VFs, found ${#vfs[@]}"
    exit 1
}
echo "OK: 2 VFs created on SR-IOV PF"

msg "disable VFs on SR-IOV PF"
echo 0 | sudo -n tee \
    "/sys/bus/pci/devices/$SRIOV_PF/sriov_numvfs" >/dev/null
sleep 1

mapfile -t vfs_after < <(find_fake_devs "$VF_DEVICE")
[ "${#vfs_after[@]}" -eq 0 ] || {
    echo "FAIL: VFs still visible after disable"
    exit 1
}
echo "OK: VFs removed"

# --- mdev PF checks ---

msg "verify mdev PF has mdev_bus entry"
MDEV_BUS="/sys/class/mdev_bus/$MDEV_PF"
[ -d "$MDEV_BUS" ] || {
    echo "FAIL: mdev PF $MDEV_PF has no mdev_bus entry"
    exit 1
}
echo "OK: $MDEV_BUS exists"

msg "verify mdev_supported_types on mdev PF"
TYPES_DIR="$MDEV_BUS/mdev_supported_types"
SMALL_DIR=$(find "$TYPES_DIR" -maxdepth 1 \
    -name '*sim_accel_small' -type d | head -1)
LARGE_DIR=$(find "$TYPES_DIR" -maxdepth 1 \
    -name '*sim_accel_large' -type d | head -1)

[ -n "$SMALL_DIR" ] || {
    echo "FAIL: sim_accel_small type not found under $TYPES_DIR"
    exit 1
}
[ -n "$LARGE_DIR" ] || {
    echo "FAIL: sim_accel_large type not found under $TYPES_DIR"
    exit 1
}
assert_file_content "$SMALL_DIR/available_instances" "4"
assert_file_content "$LARGE_DIR/available_instances" "1"

msg "verify mdev PF rejects sriov_numvfs"
if echo 1 | sudo -n tee \
    "/sys/bus/pci/devices/$MDEV_PF/sriov_numvfs" >/dev/null 2>&1; then
    echo "FAIL: mdev PF should reject sriov_numvfs write"
    exit 1
fi
echo "OK: mdev PF rejected sriov_numvfs write"

msg "create and remove mdev instance"
UUID="deadbeef-dead-beef-dead-beefdeadbeef"
echo "$UUID" | sudo -n tee "$SMALL_DIR/create" >/dev/null
sleep 1

[ -d "/sys/bus/mdev/devices/$UUID" ] || {
    echo "FAIL: mdev instance $UUID not found"
    exit 1
}
echo "OK: mdev instance $UUID created"

echo 1 | sudo -n tee "/sys/bus/mdev/devices/$UUID/remove" >/dev/null
sleep 1

[ ! -d "/sys/bus/mdev/devices/$UUID" ] || {
    echo "FAIL: mdev instance $UUID still exists after remove"
    exit 1
}
echo "OK: mdev instance $UUID removed"

# --- Cleanup ---

msg "cleanup"
LOG=/tmp/fake_pci_mixed_mode_final_cleanup.log \
    ./cleanup_fake_pci_sriov.sh

! grep -q '^fake_pci_sriov ' /proc/modules || {
    echo "FAIL: module remains loaded after cleanup"
    exit 1
}

trap - EXIT
msg "log saved to $LOG"
msg PASS
