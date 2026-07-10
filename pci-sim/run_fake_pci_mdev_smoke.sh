#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0
#
# Host-side smoke test for fake_pci_sriov mdev support.
#
# Purpose: load the module, set the PF personality to mdev, verify the mdev
# sysfs tree is correctly populated, create and remove an mdev instance, and
# clean up.
#
# Prerequisites: sudo without a password, vfio-pci and the kernel mdev
# framework (CONFIG_VFIO_MDEV), and a kernel that can load
# fake_pci_sriov.ko.
#
# Exit status is zero when all checks pass and cleanup succeeds.
set -euo pipefail

MODULE=${MODULE:-./fake_pci_sriov.ko}
MODULE_ARGS=${MODULE_ARGS:-"mdev_instances=8"}
VENDOR=${VENDOR:-0x1d55}
PF_DEVICE=${PF_DEVICE:-0x1000}
LOG=${LOG:-/tmp/fake_pci_mdev_smoke.log}

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

cleanup() {
    set +e
    msg cleanup
    LOG=/tmp/fake_pci_mdev_cleanup.log \
        ./cleanup_fake_pci_sriov.sh || true
    msg "log saved to $LOG"
}
trap cleanup EXIT

assert_file_content() {
    local path=$1 expected=$2 actual
    actual=$(cat "$path" 2>/dev/null | tr -d '[:space:]')
    echo "CHECK $path = '$actual' (expect '$expected')"
    [ "$actual" = "$expected" ] || {
        echo "FAIL: $path content '$actual', expected '$expected'"
        exit 1
    }
}

# Resolve MODULE relative to the invocation directory before the cd below,
# so 'MODULE=./pci-sim/fake_pci_sriov.ko pci-sim/run_fake_pci_mdev_smoke.sh'
# works from the repository root.
INVOKED_FROM=$PWD
cd "$(dirname "$0")"
case $MODULE in
    /*) ;;
    *) MODULE=$INVOKED_FROM/$MODULE ;;
esac
sudo -n true

if grep -q '^fake_pci_sriov ' /proc/modules ||
    [ -n "$(find_fake_devs "$PF_DEVICE")" ]; then
    LOG=/tmp/fake_pci_mdev_pre_cleanup.log \
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
[ "${#pfs[@]}" -ge 1 ] || {
    echo "FAIL: no PFs found"
    exit 1
}

PF="${pfs[0]}"

msg "set vf_personality to mdev"
echo mdev | sudo -n tee \
    "/sys/bus/pci/devices/$PF/vf_personality" >/dev/null
sleep 1

MDEV_BUS="/sys/class/mdev_bus/$PF"

msg "verify mdev_bus entry exists"
[ -d "$MDEV_BUS" ] || {
    echo "FAIL: $MDEV_BUS does not exist"
    exit 1
}
echo "OK: $MDEV_BUS exists"

msg "verify mdev_supported_types"
TYPES_DIR="$MDEV_BUS/mdev_supported_types"
[ -d "$TYPES_DIR" ] || {
    echo "FAIL: $TYPES_DIR does not exist"
    exit 1
}

SMALL_DIR=$(find "$TYPES_DIR" -maxdepth 1 \
    -name '*sim_accel_small' -type d | head -1)
LARGE_DIR=$(find "$TYPES_DIR" -maxdepth 1 \
    -name '*sim_accel_large' -type d | head -1)

[ -n "$SMALL_DIR" ] || {
    echo "FAIL: sim_accel_small type not found under $TYPES_DIR"
    ls -la "$TYPES_DIR"/
    exit 1
}
[ -n "$LARGE_DIR" ] || {
    echo "FAIL: sim_accel_large type not found under $TYPES_DIR"
    ls -la "$TYPES_DIR"/
    exit 1
}
echo "SMALL_TYPE=$(basename "$SMALL_DIR")"
echo "LARGE_TYPE=$(basename "$LARGE_DIR")"

msg "verify type attributes"
assert_file_content "$SMALL_DIR/device_api" "vfio-pci"
assert_file_content "$LARGE_DIR/device_api" "vfio-pci"
assert_file_content "$SMALL_DIR/available_instances" "8"
assert_file_content "$LARGE_DIR/available_instances" "2"

[ -f "$SMALL_DIR/name" ] && echo "SMALL_NAME=$(cat "$SMALL_DIR/name")"
[ -f "$LARGE_DIR/name" ] && echo "LARGE_NAME=$(cat "$LARGE_DIR/name")"

msg "create mdev instance"
UUID="deadbeef-dead-beef-dead-beefdeadbeef"
echo "$UUID" | sudo -n tee "$SMALL_DIR/create" >/dev/null
sleep 1

[ -d "/sys/bus/mdev/devices/$UUID" ] || {
    echo "FAIL: mdev instance $UUID not found on mdev bus"
    exit 1
}
echo "OK: mdev instance $UUID created"

AVAIL_AFTER=$(cat "$SMALL_DIR/available_instances" | tr -d '[:space:]')
echo "available_instances after create: $AVAIL_AFTER"
[ "$AVAIL_AFTER" = "7" ] || {
    echo "FAIL: available_instances should be 7 after create, got $AVAIL_AFTER"
    exit 1
}

msg "remove mdev instance"
echo 1 | sudo -n tee "/sys/bus/mdev/devices/$UUID/remove" >/dev/null
sleep 1

[ ! -d "/sys/bus/mdev/devices/$UUID" ] || {
    echo "FAIL: mdev instance $UUID still exists after remove"
    exit 1
}
echo "OK: mdev instance $UUID removed"

AVAIL_RESTORED=$(cat "$SMALL_DIR/available_instances" | tr -d '[:space:]')
echo "available_instances after remove: $AVAIL_RESTORED"
[ "$AVAIL_RESTORED" = "8" ] || {
    echo "FAIL: available_instances should be 8" \
        "after remove, got $AVAIL_RESTORED"
    exit 1
}

msg "cleanup"
LOG=/tmp/fake_pci_mdev_final_cleanup.log \
    ./cleanup_fake_pci_sriov.sh

! grep -q '^fake_pci_sriov ' /proc/modules || {
    echo "FAIL: module remains loaded after cleanup"
    exit 1
}

trap - EXIT
msg "log saved to $LOG"
msg PASS
