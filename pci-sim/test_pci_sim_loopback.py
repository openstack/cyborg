#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
"""Basic host-side loopback test for ./fake_pci_sriov.ko.

The test finds the fake PF, enables VFs through sriov_numvfs, waits for the
host-side tty devices, then verifies that bytes written to each tty are read
back from the same tty.
"""

import argparse
import errno
import os
import select
import subprocess
import sys
import termios
import time
import tty

from pathlib import Path


MODULE_NAME = "fake_pci_sriov"
DEFAULT_MODULE = str(Path(__file__).resolve().with_name("fake_pci_sriov.ko"))

VENDOR = "0x1d55"
PF_DEVICE = "0x1000"
TTY_PREFIX = "/dev/ttyPCI_SIM"


def run(cmd, check=True):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def module_loaded():
    try:
        with open("/proc/modules", encoding="utf-8") as fp:
            return any(line.split()[0] == MODULE_NAME for line in fp)
    except FileNotFoundError:
        return False


def module_refcnt():
    path = Path(f"/sys/module/{MODULE_NAME}/refcnt")
    if not path.exists():
        return None
    return int(path.read_text().strip())


def read_text(path):
    return Path(path).read_text().strip().lower()


def find_pf():
    for dev in sorted(Path("/sys/bus/pci/devices").iterdir()):
        try:
            if (
                read_text(dev / "vendor") == VENDOR
                and read_text(dev / "device") == PF_DEVICE
            ):
                return dev
        except FileNotFoundError:
            continue
    return None


def wait_for_pf(timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pf = find_pf()
        if pf:
            return pf
        time.sleep(0.1)
    raise TimeoutError("fake PCI PF 1d55:1000 did not appear")


def wait_for_no_pf(timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not find_pf():
            return
        time.sleep(0.1)
    raise TimeoutError("fake PCI PF did not disappear")


def set_numvfs(pf, num_vfs):
    sriov_numvfs = pf / "sriov_numvfs"
    if sriov_numvfs.exists():
        sriov_numvfs.write_text(f"{num_vfs}\n")


def remove_fake_pf(timeout):
    pf = find_pf()
    if not pf:
        return

    try:
        set_numvfs(pf, 0)
    except Exception as exc:
        print(
            f"warning: failed to disable VFs before remove: {exc}",
            file=sys.stderr,
        )

    remove = pf / "remove"
    if remove.exists():
        remove.write_text("1\n")
        wait_for_no_pf(timeout)


def unload_module(timeout, force_remove_pf=False):
    if not module_loaded():
        return

    if force_remove_pf:
        remove_fake_pf(timeout)

    refcnt = module_refcnt()
    if refcnt not in (None, 0):
        remove_fake_pf(timeout)

    ret = run(["rmmod", MODULE_NAME], check=False)
    if ret.returncode != 0:
        raise RuntimeError(
            f"failed to unload {MODULE_NAME}: {ret.stderr.strip() or ret.stdout.strip()} "
            f"(refcnt={module_refcnt()})"
        )


def load_module(module_path, timeout, reload_existing=False):
    if module_loaded():
        if not reload_existing:
            print(f"{MODULE_NAME} already loaded; reusing existing module")
            return
        unload_module(timeout, force_remove_pf=True)

    # fake_pci_sriov uses vfio_pci_core symbols.  insmod does not resolve
    # dependencies, so preload the VFIO PCI stack for standalone builds.
    run(["modprobe", "vfio-pci"])
    run(["insmod", module_path])
    wait_for_pf(timeout)


def wait_for_ttys(count, timeout):
    deadline = time.monotonic() + timeout
    paths = [Path(f"{TTY_PREFIX}{i}") for i in range(count)]
    while time.monotonic() < deadline:
        if all(p.exists() for p in paths):
            return paths
        time.sleep(0.1)
    missing = [str(p) for p in paths if not p.exists()]
    raise TimeoutError(f"TTY devices did not appear: {', '.join(missing)}")


def set_raw(fd):
    attrs = termios.tcgetattr(fd)
    tty.setraw(fd)
    return attrs


def restore_termios(fd, attrs):
    try:
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
    except OSError:
        pass


def read_exact(fd, size, timeout):
    deadline = time.monotonic() + timeout
    data = bytearray()
    while len(data) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        r, _, _ = select.select([fd], [], [], remaining)
        if not r:
            break
        try:
            chunk = os.read(fd, size - len(data))
        except BlockingIOError:
            continue
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)


def test_tty(path, payload, timeout):
    fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    old_attrs = None
    try:
        old_attrs = set_raw(fd)
        # Drain any stale data from a previous failed run.
        while True:
            try:
                if not os.read(fd, 4096):
                    break
            except BlockingIOError:
                break
            except OSError as exc:
                if exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    break
                raise

        written = os.write(fd, payload)
        if written != len(payload):
            raise RuntimeError(
                f"short write to {path}: {written}/{len(payload)}"
            )

        got = read_exact(fd, len(payload), timeout)
        if got != payload:
            raise RuntimeError(
                f"loopback mismatch on {path}: got {got!r}, expected {payload!r}"
            )
    finally:
        if old_attrs is not None:
            restore_termios(fd, old_attrs)
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--module",
        default=DEFAULT_MODULE,
        help="module path for --load/--reload",
    )
    parser.add_argument(
        "--load",
        "--insmod",
        dest="load",
        action="store_true",
        help="load the module before testing; reuse it if already loaded",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="deterministically remove any existing fake PF/module, then insmod",
    )
    parser.add_argument(
        "--unload",
        "--rmmod",
        dest="unload",
        action="store_true",
        help="remove fake PF and rmmod the module after testing",
    )
    parser.add_argument(
        "--vfs", type=int, default=2, help="number of VFs to enable"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="wait/read timeout in seconds",
    )
    parser.add_argument(
        "--keep-vfs",
        action="store_true",
        help="leave VFs enabled after the test",
    )
    args = parser.parse_args()

    if args.reload:
        load_module(args.module, args.timeout, reload_existing=True)
    elif args.load:
        load_module(args.module, args.timeout, reload_existing=False)

    pf = wait_for_pf(args.timeout)
    print(f"PF: {pf.name}")

    try:
        # Start from a known VF state even when reusing an existing module.
        set_numvfs(pf, 0)
        pf = wait_for_pf(args.timeout)
        set_numvfs(pf, args.vfs)

        ttys = wait_for_ttys(args.vfs, args.timeout)
        for i, path in enumerate(ttys):
            payload = f"pci-sim-vf{i}-hello\n".encode()
            test_tty(str(path), payload, args.timeout)
            print(f"ok: {path} echoed {payload!r}")
    finally:
        if args.unload:
            unload_module(args.timeout, force_remove_pf=True)
        elif not args.keep_vfs:
            try:
                pf = find_pf()
                if pf:
                    set_numvfs(pf, 0)
            except Exception as exc:
                print(
                    f"warning: failed to disable VFs: {exc}", file=sys.stderr
                )

    print("PASS")


if __name__ == "__main__":
    main()
