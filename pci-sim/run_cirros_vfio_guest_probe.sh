#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0
#
# Boot a CirrOS guest with one fake_pci_sriov VF assigned through VFIO and run
# guest-side discovery commands from the serial console.
#
# Prerequisites:
# - qemu-system-x86_64, python3, curl, timeout, sudo without a password
# - a kernel that can load fake_pci_sriov.ko and vfio-pci
# - a CirrOS qcow2 image, downloaded automatically when IMAGE is missing
#
# Important environment variables:
# - MODULE: fake_pci_sriov module path, default ./fake_pci_sriov.ko
# - MODULE_ARGS: optional arguments passed to insmod
# - RELOAD_MODULE: remove an existing fake_pci_sriov instance first, default 1
# - IMAGE: CirrOS image path, default /tmp/cirros-0.6.3-x86_64-disk.img
# - IMAGE_URL: URL used to download IMAGE when it is absent
# - VENDOR/PF_DEVICE/VF_DEVICE: fake PCI IDs, defaults 0x1d55/0x1000/0x1001
# - QEMU_DEADLINE: seconds to wait for the guest probe, default 120
# - LOG: log file, default /tmp/cirros_vfio_guest_probe.log
#
# Flow: preflight, ensure image, reload/load module, create one VF, bind the VF
# to pci_sim_vfio_pci, launch QEMU with a user-mode NIC so CirrOS reaches the
# login prompt, log in to CirrOS, and run guest probes.
# Exit status is zero only when the guest prints GUEST_PROBE_END.
#
# Example:
#   sudo -n true && bash pci-sim/run_cirros_vfio_guest_probe.sh
set -euo pipefail

MODULE=${MODULE:-./fake_pci_sriov.ko}
MODULE_ARGS=${MODULE_ARGS:-}
RELOAD_MODULE=${RELOAD_MODULE:-1}
IMAGE=${IMAGE:-/tmp/cirros-0.6.3-x86_64-disk.img}
IMAGE_URL=${IMAGE_URL:-https://github.com/cirros-dev/cirros/releases/download/0.6.3/cirros-0.6.3-x86_64-disk.img}
VENDOR=${VENDOR:-0x1d55}
PF_DEVICE=${PF_DEVICE:-0x1000}
VF_DEVICE=${VF_DEVICE:-0x1001}
LOG=${LOG:-/tmp/cirros_vfio_guest_probe.log}
QEMU_DEADLINE=${QEMU_DEADLINE:-120}

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
	msg cleanup
	if [ -n "${VF:-}" ] && [ -e "/sys/bus/pci/devices/$VF" ]; then
		if [ -e "/sys/bus/pci/devices/$VF/driver/unbind" ]; then
			echo "$VF" | sudo -n tee "/sys/bus/pci/devices/$VF/driver/unbind" >/dev/null
		fi
		echo '' | sudo -n tee "/sys/bus/pci/devices/$VF/driver_override" >/dev/null
	fi
	if [ -n "${PF:-}" ] && [ -e "/sys/bus/pci/devices/$PF/sriov_numvfs" ]; then
		echo 0 | sudo -n tee "/sys/bus/pci/devices/$PF/sriov_numvfs" >/dev/null
	fi
	msg "log saved to $LOG"
}
trap cleanup EXIT

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

msg preflight
command -v qemu-system-x86_64
command -v python3
sudo -n true

msg "ensure CirrOS image"
if [ ! -s "$IMAGE" ]; then
	timeout 180s curl -L --fail --connect-timeout 20 \
		-o "$IMAGE.tmp" "$IMAGE_URL"
	mv "$IMAGE.tmp" "$IMAGE"
fi

msg "prepare VFIO and fake PCI module"
sudo -n modprobe vfio-pci
if grep -q '^fake_pci_sriov ' /proc/modules && [ "$RELOAD_MODULE" = 1 ]; then
	old_pf=$(find_dev "$PF_DEVICE" || true)
	if [ -n "$old_pf" ]; then
		echo 1 | sudo -n tee "/sys/bus/pci/devices/$old_pf/remove" >/dev/null || true
	fi
	sudo -n rmmod fake_pci_sriov || true
fi
if ! grep -q '^fake_pci_sriov ' /proc/modules; then
	msg "insmod $MODULE $MODULE_ARGS"
	# shellcheck disable=SC2086
	sudo -n insmod "$MODULE" $MODULE_ARGS
fi

msg "create one VF"
PF=$(find_dev "$PF_DEVICE")
msg "PF=$PF"
echo 0 | sudo -n tee "/sys/bus/pci/devices/$PF/sriov_numvfs" >/dev/null || true
echo 1 | sudo -n tee "/sys/bus/pci/devices/$PF/sriov_numvfs" >/dev/null
sleep 1
VF=$(find_dev "$VF_DEVICE")
msg "VF=$VF"

msg "bind VF to pci_sim_vfio_pci"
if [ -e /sys/module/vfio_iommu_type1/parameters/allow_unsafe_interrupts ]; then
	echo Y | sudo -n tee \
		/sys/module/vfio_iommu_type1/parameters/allow_unsafe_interrupts >/dev/null
fi
if [ -e "/sys/bus/pci/devices/$VF/driver/unbind" ]; then
	echo "$VF" | sudo -n tee "/sys/bus/pci/devices/$VF/driver/unbind" >/dev/null
fi
echo pci_sim_vfio_pci | sudo -n tee "/sys/bus/pci/devices/$VF/driver_override" >/dev/null
echo "$VF" | sudo -n tee /sys/bus/pci/drivers_probe >/dev/null
readlink -f "/sys/bus/pci/devices/$VF/driver"

msg "boot CirrOS and run guest probe"
export IMAGE VF QEMU_DEADLINE
python3 "$SCRIPT_DIR/run_cirros_vfio_guest_probe.py"
msg PASS
