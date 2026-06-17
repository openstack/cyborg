#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
"""Monitor a CirrOS config-drive guest UART end-to-end test.

This helper is launched by ``run_cirros_vfio_userdata_echo.sh`` after the
shell wrapper has built a config-drive, loaded ``fake_pci_sriov``, created one
VF, and bound that VF to ``pci_sim_vfio_pci``.  The config-drive user-data
script runs inside the guest and prints ``E2E_END`` when it finishes.  This
helper starts QEMU, mirrors serial output to stdout, and fails if the guest
reports ``E2E_FAIL`` or the end marker is not seen before the deadline.

Usage::

    IMAGE=/tmp/cirros.img VF=0000:00:01.1 CONFIG_ISO=/tmp/configdrive.iso \
        QEMU_DEADLINE=150 python3 run_cirros_vfio_userdata_echo.py

Environment variables:

* ``IMAGE``: required CirrOS qcow2 image path.
* ``VF``: required PCI address of the VF bound to ``pci_sim_vfio_pci``.
* ``CONFIG_ISO``: required config-drive ISO path containing the guest user-data
  script.
* ``QEMU_DEADLINE``: maximum seconds to wait for ``E2E_END``; defaults to
  ``150``.
"""

from __future__ import annotations

import os
import pty
import select
import subprocess
import sys
import time


MONITOR_INTERVAL = 0.5


def launch_qemu(
    image: str,
    vf: str,
    config_iso: str,
) -> tuple[subprocess.Popen[bytes], int]:
    """Launch QEMU with ``vf`` assigned and ``config_iso`` attached."""
    cmd = [
        "sudo",
        "-n",
        "qemu-system-x86_64",
        "-nodefaults",
        "-display",
        "none",
        "-serial",
        "stdio",
        "-monitor",
        "none",
        "-machine",
        "q35,accel=kvm",
        "-cpu",
        "host",
        "-smp",
        "1",
        "-m",
        "512M",
        "-snapshot",
        "-drive",
        f"file={image},if=virtio,format=qcow2",
        "-drive",
        f"file={config_iso},if=virtio,media=cdrom,readonly=on,format=raw",
        "-netdev",
        "user,id=n0",
        "-device",
        "virtio-net-pci,netdev=n0",
        "-device",
        f"vfio-pci,host={vf}",
        "-no-reboot",
    ]
    print("+ " + " ".join(cmd), flush=True)
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        cmd, stdin=slave, stdout=slave, stderr=slave, close_fds=True
    )
    os.close(slave)
    return proc, master


def monitor_e2e_output(
    proc: subprocess.Popen[bytes],
    master: int,
    deadline: int,
) -> tuple[bool, str]:
    """Mirror console output until ``E2E_END``, process exit, or deadline."""
    buf = ""
    success = False
    end = time.monotonic() + deadline

    while time.monotonic() < end:
        rlist, _, _ = select.select([master], [], [], MONITOR_INTERVAL)
        if rlist:
            try:
                data = os.read(master, 4096)
            except OSError:
                break
            if not data:
                break
            text = data.decode(errors="replace")
            sys.stdout.write(text)
            sys.stdout.flush()
            buf += text
            if "E2E_END" in buf:
                success = True
                break
        if proc.poll() is not None and not rlist:
            break
    return success, buf


def stop_qemu(proc: subprocess.Popen[bytes]) -> None:
    """Terminate QEMU, escalating to kill if it does not exit promptly."""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def main() -> None:
    """Run the guest user-data echo test and exit non-zero on failure."""
    image = os.environ["IMAGE"]
    vf = os.environ["VF"]
    config_iso = os.environ["CONFIG_ISO"]
    deadline = int(os.environ.get("QEMU_DEADLINE", "150"))

    proc, master = launch_qemu(image, vf, config_iso)
    try:
        success, buf = monitor_e2e_output(proc, master, deadline)
    finally:
        stop_qemu(proc)
        os.close(master)

    print(f"\nQEMU_RC={proc.returncode}")
    if not success:
        sys.exit("FAIL: E2E_END not seen")
    if "E2E_FAIL" in buf:
        sys.exit("FAIL: guest reported E2E_FAIL")


if __name__ == "__main__":
    main()
