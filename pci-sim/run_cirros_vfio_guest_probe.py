#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
"""Boot a CirrOS guest with one fake VF and run probe commands.

This helper is launched by ``run_cirros_vfio_guest_probe.sh`` after the
shell wrapper has loaded ``fake_pci_sriov``, created one VF, and bound that
VF to ``pci_sim_vfio_pci``.  It owns the interactive QEMU console handling:
wait for the CirrOS login prompt, log in, run guest-side PCI/TTY probes, and
fail if the probe marker is not seen before the deadline.

Usage::

    IMAGE=/tmp/cirros.img VF=0000:00:01.1 QEMU_DEADLINE=120 \
        python3 run_cirros_vfio_guest_probe.py

Environment variables:

* ``IMAGE``: required CirrOS qcow2 image path.
* ``VF``: required PCI address of the VF bound to ``pci_sim_vfio_pci``.
* ``QEMU_DEADLINE``: maximum seconds to wait for the guest probe; defaults to
  ``120``.
"""

from __future__ import annotations

import os
import pty
import re
import select
import subprocess
import sys
import time


GUEST_COMMANDS = (
    r"""
echo GUEST_PROBE_BEGIN
for d in /sys/bus/pci/devices/*; do
    echo DEV=$d vendor=$(cat $d/vendor) \
        device=$(cat $d/device) class=$(cat $d/class)
    cat $d/resource 2>/dev/null | head -1
done
ls -l /dev/ttyS* 2>/dev/null || true
sudo dmesg | grep -Ei '1d55|1001|1d0f|8250|10a9|0003|serial|ttyS' || true
for t in /dev/ttyS1 /dev/ttyS2 /dev/ttyS3 /dev/ttyS4; do
    [ -e $t ] && echo TRY_TTY=$t && \
        sudo stty -F $t raw -echo 9600 2>&1 && \
        sudo sh -c "echo -n hello > $t" 2>&1 && \
        timeout 2 sudo dd bs=1 count=5 if=$t 2>/dev/null | hexdump -C
done
echo GUEST_PROBE_END
"""
    + "\n"
)


def launch_qemu(image: str, vf: str) -> tuple[subprocess.Popen[bytes], int]:
    """Launch QEMU with ``vf`` assigned and return the process and PTY FD."""
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


def send(master: int, text: str) -> None:
    """Send ``text`` to the QEMU serial console PTY."""
    os.write(master, text.encode())


def read_console(master: int, timeout: float = 0.5) -> str:
    """Read available QEMU console output for up to ``timeout`` seconds."""
    out = b""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        rlist, _, _ = select.select(
            [master], [], [], max(0, end - time.monotonic())
        )
        if not rlist:
            break
        try:
            chunk = os.read(master, 4096)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
        if len(chunk) < 4096:
            break
    return out.decode(errors="replace")


def run_guest_commands(
    proc: subprocess.Popen[bytes],
    master: int,
    deadline_s: int,
) -> bool:
    """Log in to CirrOS, run probe commands, and return success status."""
    buf = ""
    logged = False
    sent = False
    end = time.monotonic() + deadline_s

    while time.monotonic() < end:
        output = read_console(master)
        if output:
            sys.stdout.write(output)
            sys.stdout.flush()
            buf += output

        if not logged and re.search(r"(?:^|[\r\n])[^\r\n]* login:\s*$", buf):
            send(master, "cirros\n")
            buf = ""
            continue
        if not logged and re.search(r"(?:^|[\r\n])Password:\s*$", buf):
            send(master, "gocubsgo\n")
            logged = True
            buf = ""
            time.sleep(1)
            continue
        if logged and not sent and ("$ " in buf or "# " in buf):
            send(master, GUEST_COMMANDS)
            sent = True
            buf = ""
            continue
        if "GUEST_PROBE_END" in buf:
            return True
        if proc.poll() is not None:
            break
    return False


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
    """Run the CirrOS guest probe and exit non-zero on failure."""
    image = os.environ["IMAGE"]
    vf = os.environ["VF"]
    deadline_s = int(os.environ.get("QEMU_DEADLINE", "120"))

    proc, master = launch_qemu(image, vf)
    try:
        success = run_guest_commands(proc, master, deadline_s)
    finally:
        stop_qemu(proc)
        os.close(master)

    print(f"\nQEMU_RC={proc.returncode}")
    if not success:
        sys.exit("FAIL: guest probe did not complete")


if __name__ == "__main__":
    main()
