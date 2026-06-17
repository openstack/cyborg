#!/bin/sh
# SPDX-License-Identifier: GPL-2.0
#
# CirrOS config-drive user-data for run_cirros_vfio_userdata_echo.sh.
#
# This script runs inside the CirrOS guest.  It discovers the fake PCI VF that
# QEMU passed through with VFIO, prints PCI and serial-driver diagnostics to the
# serial console, and verifies that the emulated UART loopback path can echo an
# alphabet string through one of the guest ttyS devices.

exec </dev/console >/dev/ttyS0 2>&1
echo E2E_BEGIN
PATH=/sbin:/bin:/usr/sbin:/usr/bin
DEV=""
for d in /sys/bus/pci/devices/*; do
  v=$(cat $d/vendor 2>/dev/null || true)
  p=$(cat $d/device 2>/dev/null || true)
  if { [ "$v" = "0x1d55" ] && [ "$p" = "0x1001" ]; } || { [ "$v" = "0x1d0f" ] && [ "$p" = "0x8250" ]; } || { [ "$v" = "0x10a9" ] && [ "$p" = "0x0003" ]; }; then DEV=$d; break; fi
done
echo DEV=$DEV
if [ -n "$DEV" ]; then
  echo VENDOR=$(cat $DEV/vendor) DEVICE=$(cat $DEV/device) CLASS=$(cat $DEV/class)
  echo RESOURCE0=$(head -n1 $DEV/resource)
  BASE=$(awk 'NR==1 {print $1}' $DEV/resource)
  echo BASE=$BASE
  UART_OFFSET=0
  [ "$(cat $DEV/vendor)" = "0x10a9" ] && [ "$(cat $DEV/device)" = "0x0003" ] && UART_OFFSET=0x20178
  UART_BASE=$(printf "0x%x" $((BASE + UART_OFFSET)))
  echo UART_OFFSET=$UART_OFFSET UART_BASE=$UART_BASE
else
  echo NO_FAKE_VF
fi
echo TTY_LIST_BEGIN
ls -l /dev/ttyS* 2>&1 || true
echo TTY_LIST_END
echo DMESG_MATCH_BEGIN
dmesg | grep -Ei '1d55|1001|1d0f|8250|10a9|0003|serial|ttyS' || true
echo DMESG_MATCH_END
if [ -n "$DEV" ] && command -v devmem >/dev/null 2>&1; then
  echo DEVMEM_PRESENT
  # 16550 offsets: THR/RBR=0, LSR=5.  This is a smoke test for trapped MMIO.
  LSR_ADDR=$(printf "0x%x" $((UART_BASE + 5)))
  THR_ADDR=$(printf "0x%x" $((UART_BASE + 0)))
  echo LSR_BEFORE=$(devmem $LSR_ADDR 8 2>&1 || true)
  echo WRITE_THR_A=$(devmem $THR_ADDR 8 0x41 2>&1 || true)
  echo LSR_AFTER=$(devmem $LSR_ADDR 8 2>&1 || true)
  echo RBR_READ=$(devmem $THR_ADDR 8 2>&1 || true)
  echo TTY_ALPHABET_BEGIN
  TTY_PASS=0
  TEST_STR=ABCDEFGHIJKLMNOPQRSTUVWXYZ
  for t in /dev/ttyS32 /dev/ttyS33 /dev/ttyS34 /dev/ttyS35 /dev/ttyS1 /dev/ttyS2 /dev/ttyS3 /dev/ttyS4; do
    [ -e $t ] || continue
    echo TRY_TTY=$t
    if (
      exec 7<>$t || exit 1
      stty -F $t raw -echo -icanon clocal -hupcl min 0 time 20 9600 2>&1 || exit 1
      printf "%s" "$TEST_STR" >&7
      TTY_READ=$(dd bs=1 count=26 <&7 2>/dev/null || true)
      echo TTY_SELECTED=$t
      echo TTY_EXPECT=$TEST_STR
      echo TTY_READ=$TTY_READ
      echo TTY_READ_HEXDUMP_BEGIN
      printf "%s" "$TTY_READ" | hexdump -C || true
      echo TTY_READ_HEXDUMP_END
      [ "$TTY_READ" = "$TEST_STR" ] || exit 1
      exec 7>&-
    ) 2>&1; then
      TTY_PASS=1
      echo TTY_ALPHABET_PASS=$t
      break
    fi
  done
  if [ "$TTY_PASS" != 1 ]; then
    echo TTY_ALPHABET_FAIL
    echo E2E_FAIL
  fi
  echo TTY_ALPHABET_END
else
  echo DEVMEM_MISSING_OR_NO_DEV
fi
echo E2E_END
sync
poweroff -f
