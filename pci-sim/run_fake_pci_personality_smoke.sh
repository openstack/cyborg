#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0
#
# Host-side smoke test for the per-PF vf_personality sysfs interface.
#
# Purpose: load the module with two PFs, verify the vf_personality and
# vf_personality_available sysfs files exist and work correctly, test VF
# creation under the uart personality, verify personality changes are
# rejected while VFs are active, and confirm invalid personality names
# are rejected.
#
# Prerequisites: sudo without a password and a kernel that can load
# fake_pci_sriov.ko.
#
# Exit status is zero when all checks pass and cleanup succeeds.
set -euo pipefail

MODULE=${MODULE:-./fake_pci_sriov.ko}
MODULE_ARGS=${MODULE_ARGS:-"num_pfs=2"}
VENDOR=${VENDOR:-0x1d55}
PF_DEVICE=${PF_DEVICE:-0x1000}
VF_DEVICE=${VF_DEVICE:-0x1001}
LOG=${LOG:-/tmp/fake_pci_personality_smoke.log}

: >"$LOG"
exec > >(tee -a "$LOG") 2>&1

msg() { echo "== $* =="; }

fail() { echo "FAIL: $*"; exit 1; }

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
    LOG=/tmp/fake_pci_personality_cleanup.log \
        ./cleanup_fake_pci_sriov.sh || true
    msg "log saved to $LOG"
}
trap cleanup EXIT

cd "$(dirname "$0")"
sudo -n true

if grep -q '^fake_pci_sriov ' /proc/modules ||
    [ -n "$(find_fake_devs "$PF_DEVICE")" ]; then
    LOG=/tmp/fake_pci_personality_pre_cleanup.log \
        ./cleanup_fake_pci_sriov.sh || true
fi

msg "preload VFIO dependencies"
sudo -n modprobe vfio-pci

msg "insmod $MODULE $MODULE_ARGS"
# shellcheck disable=SC2086
sudo -n insmod "$MODULE" $MODULE_ARGS
sleep 1

mapfile -t pfs < <(find_fake_devs "$PF_DEVICE")
printf 'PF_LIST=%s\n' "${pfs[*]}"
[ "${#pfs[@]}" -eq 2 ] || fail "expected 2 PFs, found ${#pfs[@]}"

PF0="${pfs[0]}"
PF1="${pfs[1]}"

# --- Verify sysfs personality files exist ---

msg "verify sysfs personality files exist"
for pf in "${pfs[@]}"; do
    path="/sys/bus/pci/devices/$pf"
    [ -f "$path/vf_personality" ] || fail "missing vf_personality on $pf"
    [ -f "$path/vf_personality_available" ] || \
        fail "missing vf_personality_available on $pf"
done
echo "OK: sysfs personality files present on all PFs"

# --- Verify default personality ---

msg "verify default personality is unset"
pers=$(cat "/sys/bus/pci/devices/$PF0/vf_personality")
[ "$pers" = "unset" ] || fail "expected unset, got '$pers'"
echo "OK: default personality is unset"

msg "verify available personalities"
avail=$(cat "/sys/bus/pci/devices/$PF0/vf_personality_available")
echo "vf_personality_available=$avail"
echo "$avail" | grep -q '\[unset\]' || \
    fail "expected [unset] in available, got '$avail'"
echo "OK: available personalities list is correct"

# --- Verify sriov_numvfs rejected with unset personality ---

msg "verify unset PF rejects sriov_numvfs"
if echo 1 | sudo -n tee \
    "/sys/bus/pci/devices/$PF0/sriov_numvfs" >/dev/null 2>&1; then
    fail "unset PF should reject sriov_numvfs write"
fi
echo "OK: unset PF rejected sriov_numvfs write"

# --- VFs work under uart personality ---

msg "set PF0 personality to uart"
echo uart | sudo -n tee \
    "/sys/bus/pci/devices/$PF0/vf_personality" >/dev/null

msg "verify available marker moved to uart"
avail=$(cat "/sys/bus/pci/devices/$PF0/vf_personality_available")
echo "vf_personality_available=$avail"
echo "$avail" | grep -q '\[uart\]' || \
    fail "expected [uart] in available, got '$avail'"
if echo "$avail" | grep -q '\[unset\]'; then
    fail "expected unset to be unmarked, got '$avail'"
fi
echo "OK: available marker moved to uart"

msg "enable VFs on uart PF"
echo 2 | sudo -n tee \
    "/sys/bus/pci/devices/$PF0/sriov_numvfs" >/dev/null
sleep 1

mapfile -t vfs < <(find_fake_devs "$VF_DEVICE")
printf 'VF_LIST=%s\n' "${vfs[*]}"
[ "${#vfs[@]}" -eq 2 ] || fail "expected 2 VFs, found ${#vfs[@]}"
echo "OK: 2 VFs created on uart PF"

# --- Reject personality change while VFs are active ---

msg "verify personality change rejected while VFs active"
if echo uart | sudo -n tee \
    "/sys/bus/pci/devices/$PF0/vf_personality" >/dev/null 2>&1; then
    fail "should reject vf_personality write while VFs active"
fi
echo "OK: personality change rejected while VFs active"

# --- Disable VFs ---

msg "disable VFs"
echo 0 | sudo -n tee \
    "/sys/bus/pci/devices/$PF0/sriov_numvfs" >/dev/null
sleep 1

mapfile -t vfs_after < <(find_fake_devs "$VF_DEVICE")
[ "${#vfs_after[@]}" -eq 0 ] || fail "VFs still visible after disable"
echo "OK: VFs removed"

# --- Reject invalid personality ---

msg "verify invalid personality rejected"
if echo bogus | sudo -n tee \
    "/sys/bus/pci/devices/$PF0/vf_personality" >/dev/null 2>&1; then
    fail "should reject unknown personality name"
fi
echo "OK: invalid personality rejected"

# --- Cleanup ---

msg "cleanup"
LOG=/tmp/fake_pci_personality_final_cleanup.log \
    ./cleanup_fake_pci_sriov.sh

! grep -q '^fake_pci_sriov ' /proc/modules || \
    fail "module remains loaded after cleanup"

[ -z "$(find_fake_devs "$PF_DEVICE")$(find_fake_devs "$VF_DEVICE")" ] || \
    fail "fake PCI devices still visible after cleanup"

trap - EXIT
msg "log saved to $LOG"
msg PASS
