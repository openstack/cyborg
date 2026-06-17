#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Create pci-sim Nova and Cyborg test servers one at a time and validate the
# VF-backed serial echo device inside CirrOS over SSH.

set -eo pipefail

OS_CLOUD_NAME=${OS_CLOUD_NAME:-devstack-admin}
IMAGE=${IMAGE:-cirros-0.6.3-x86_64-disk}
NETWORK=${NETWORK:-private}
PUBLIC_NETWORK=${PUBLIC_NETWORK:-public}
NOVA_FLAVOR=${NOVA_FLAVOR:-pci-sim-nova}
CYBORG_FLAVOR=${CYBORG_FLAVOR:-pci-sim-cyborg}
NOVA_SERVER=${NOVA_SERVER:-pci-sim-test-nova-serial}
CYBORG_SERVER=${CYBORG_SERVER:-pci-sim-test-cyborg-serial}
SSH_USER=${SSH_USER:-cirros}
SSH_PASSWORD=${SSH_PASSWORD:-gocubsgo}
SSH_TIMEOUT=${SSH_TIMEOUT:-240}
BUILD_TIMEOUT=${BUILD_TIMEOUT:-240}
FLOATING_IP_TAG=${FLOATING_IP_TAG:-pci-sim-serial-echo-test}
KEEP=${KEEP:-0}
CLEANUP_ONLY=0
RUN_NOVA=1
RUN_CYBORG=1

usage() {
    cat <<EOF
Usage: $0 [options]

Create pci-sim test VMs serially, validate the passed-through VF-backed serial
port from inside CirrOS, and clean up the VMs and floating IPs afterwards.

The script assumes DevStack has already created the image, flavors, device
profile, Nova PCI config, and Cyborg PCI config.

By default this uses ``openstack --os-cloud devstack-admin`` and does not
require sourcing ``openrc``:

  $0

Defaults create one VM at a time on the private network and attach a temporary
floating IP from the public network. The default security group for the current
project is opened for ICMP and SSH.

Options:
  --os-cloud NAME           clouds.yaml cloud name (default: $OS_CLOUD_NAME)
  --image NAME              Image to boot (default: $IMAGE)
  --network NAME            Tenant network for the VM (default: $NETWORK)
  --public-network NAME     External network for floating IPs (default: $PUBLIC_NETWORK)
  --nova-flavor NAME        Nova PCI flavor (default: $NOVA_FLAVOR)
  --cyborg-flavor NAME      Cyborg flavor (default: $CYBORG_FLAVOR)
  --nova-server NAME        Nova test server name (default: $NOVA_SERVER)
  --cyborg-server NAME      Cyborg test server name (default: $CYBORG_SERVER)
  --ssh-user USER           Guest SSH user (default: $SSH_USER)
  --ssh-password PASSWORD   Guest SSH password (default: $SSH_PASSWORD)
  --build-timeout SECONDS   Server ACTIVE timeout (default: $BUILD_TIMEOUT)
  --ssh-timeout SECONDS     SSH readiness timeout (default: $SSH_TIMEOUT)
  --tag TAG                 Tag for temporary floating IPs (default: $FLOATING_IP_TAG)
  --nova-only               Only run the Nova flavor test
  --cyborg-only             Only run the Cyborg flavor test
  --keep                    Keep servers and floating IPs after validation
  --cleanup                 Delete test servers and floating IPs tagged by this script, then exit
  -h, --help                Show this help

Environment variables with matching uppercase names may also be used for most
options, e.g. OS_CLOUD_NAME=devstack-admin NETWORK=private PUBLIC_NETWORK=public $0.
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --os-cloud) OS_CLOUD_NAME=$2; shift 2 ;;
        --image) IMAGE=$2; shift 2 ;;
        --network) NETWORK=$2; shift 2 ;;
        --public-network) PUBLIC_NETWORK=$2; shift 2 ;;
        --nova-flavor) NOVA_FLAVOR=$2; shift 2 ;;
        --cyborg-flavor) CYBORG_FLAVOR=$2; shift 2 ;;
        --nova-server) NOVA_SERVER=$2; shift 2 ;;
        --cyborg-server) CYBORG_SERVER=$2; shift 2 ;;
        --ssh-user) SSH_USER=$2; shift 2 ;;
        --ssh-password) SSH_PASSWORD=$2; shift 2 ;;
        --build-timeout) BUILD_TIMEOUT=$2; shift 2 ;;
        --ssh-timeout) SSH_TIMEOUT=$2; shift 2 ;;
        --tag) FLOATING_IP_TAG=$2; shift 2 ;;
        --nova-only) RUN_NOVA=1; RUN_CYBORG=0; shift ;;
        --cyborg-only) RUN_NOVA=0; RUN_CYBORG=1; shift ;;
        --keep) KEEP=1; shift ;;
        --cleanup) CLEANUP_ONLY=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

require_command() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "Required command not found: $1" >&2
        exit 1
    }
}

openstack() {
    command openstack --os-cloud "$OS_CLOUD_NAME" "$@"
}

require_openstack_auth() {
    openstack token issue -f value -c id >/dev/null
}

open_default_security_group() {
    local project_id sg_id

    project_id=$(openstack token issue -f value -c project_id)
    sg_id=$(openstack security group list --project "$project_id" -f value -c ID -c Name |
        awk '$2 == "default" {print $1; exit}')
    if [[ -z $sg_id ]]; then
        echo "Could not find default security group for project $project_id" >&2
        exit 1
    fi

    echo "Opening default security group $sg_id for ICMP and SSH"
    openstack security group rule create --ingress --protocol icmp "$sg_id" >/dev/null 2>&1 || true
    openstack security group rule create --ingress --protocol tcp --dst-port 22 "$sg_id" >/dev/null 2>&1 || true
}

cleanup_resources() {
    local id name

    echo "Cleaning up test servers"
    for name in "$NOVA_SERVER" "$CYBORG_SERVER"; do
        openstack server delete "$name" >/dev/null 2>&1 || true
    done
    for _ in $(seq 1 60); do
        if ! openstack server show "$NOVA_SERVER" >/dev/null 2>&1 && \
           ! openstack server show "$CYBORG_SERVER" >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done

    echo "Deleting floating IPs tagged $FLOATING_IP_TAG"
    while read -r id; do
        [[ -n $id ]] || continue
        openstack floating ip delete "$id" >/dev/null 2>&1 || true
    done < <(openstack floating ip list --tags "$FLOATING_IP_TAG" -f value -c ID 2>/dev/null || true)
}

write_guest_probe() {
    local path=$1
    cat > "$path" <<'GUEST'
#!/bin/sh
set -u
PATH=/sbin:/bin:/usr/sbin:/usr/bin
HOST=$(hostname 2>/dev/null || true)
echo "=== GUEST $HOST uid=$(id 2>/dev/null) ==="

echo "PCI_MATCH_BEGIN"
DEV=""
for d in /sys/bus/pci/devices/*; do
    v=$(cat "$d/vendor" 2>/dev/null || true)
    p=$(cat "$d/device" 2>/dev/null || true)
    if { [ "$v" = "0x1d55" ] && [ "$p" = "0x1001" ]; } || \
       { [ "$v" = "0x10a9" ] && [ "$p" = "0x0003" ]; } || \
       { [ "$v" = "0x1d0f" ] && [ "$p" = "0x8250" ]; }; then
        DEV=$d
        echo "DEV=$DEV"
        echo "VENDOR=$v DEVICE=$p CLASS=$(cat "$d/class" 2>/dev/null || true)"
        echo "RESOURCE0=$(head -n1 "$d/resource" 2>/dev/null || true)"
    fi
done
[ -n "$DEV" ] || echo "NO_FAKE_VF"
echo "PCI_MATCH_END"

echo "DMESG_MATCH_BEGIN"
dmesg 2>/dev/null | grep -Ei '1d55|1001|10a9|0003|1d0f|8250|serial|ttyS' || true
echo "DMESG_MATCH_END"

echo "SERIAL_ECHO_BEGIN"
TEST_STR=ABCDEFGHIJKLMNOPQRSTUVWXYZ
COUNT=$(printf "%s" "$TEST_STR" | wc -c)
PASS=0
for t in /dev/ttyS32 /dev/ttyS33 /dev/ttyS34 /dev/ttyS35 \
         /dev/ttyS1 /dev/ttyS2 /dev/ttyS3 /dev/ttyS4 /dev/ttyS5 \
         /dev/ttyS6 /dev/ttyS7 /dev/ttyS8 /dev/ttyS9; do
    [ -e "$t" ] || continue
    echo "TRY_TTY=$t"
    OUT=$(
        exec 7<>"$t" || exit 1
        stty -F "$t" raw -echo -icanon clocal -hupcl min 0 time 50 9600 2>&1 || exit 1
        printf "%s" "$TEST_STR" >&7
        TTY_READ=$(dd bs=1 count="$COUNT" <&7 2>/dev/null || true)
        echo "TTY_SELECTED=$t"
        echo "TTY_EXPECT=$TEST_STR"
        echo "TTY_READ=$TTY_READ"
        [ "$TTY_READ" = "$TEST_STR" ] || exit 2
        exit 0
    )
    rc=$?
    echo "$OUT"
    if [ $rc -eq 0 ]; then
        echo "SERIAL_ECHO_PASS=$t"
        PASS=1
        break
    else
        echo "TTY_RESULT=$t rc=$rc"
    fi
done
if [ "$PASS" = 1 ]; then
    echo "SERIAL_ECHO_OK"
else
    echo "SERIAL_ECHO_FAIL"
fi
echo "SERIAL_ECHO_END"
GUEST
}

ssh_guest_probe() {
    local name=$1 ip=$2 guest_script=$3 log=$4

    python3 - "$name" "$ip" "$SSH_USER" "$SSH_PASSWORD" "$guest_script" <<'PY' | tee "$log"
import base64
import os
import pathlib
import pexpect
import sys

name, ip, user, password, guest_script = sys.argv[1:]
payload = base64.b64encode(pathlib.Path(guest_script).read_bytes()).decode()
cmd = (
    "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
    "-o PreferredAuthentications=password -o PubkeyAuthentication=no "
    "-o ConnectTimeout=10 "
    f"{user}@{ip} "
    "'base64 -d >/tmp/pci-sim-serial-echo-test.sh; "
    f"echo {password} | sudo -S sh /tmp/pci-sim-serial-echo-test.sh'"
)
print(f"===== {name} {ip} guest validation =====", flush=True)
child = pexpect.spawn(cmd, encoding="utf-8", timeout=60)
child.logfile_read = sys.stdout
try:
    while True:
        idx = child.expect([r"(?i)password:", r"(?i)yes/no", pexpect.EOF, pexpect.TIMEOUT])
        if idx == 0:
            child.sendline(password)
            break
        if idx == 1:
            child.sendline("yes")
            continue
        if idx == 2:
            raise SystemExit("SSH ended before password prompt")
        raise SystemExit("Timed out waiting for SSH password prompt")
    child.sendline(payload)
    child.sendeof()
    child.expect(pexpect.EOF, timeout=120)
finally:
    child.close()
if child.exitstatus != 0:
    raise SystemExit(child.exitstatus or 1)
PY
}

wait_for_active() {
    local name=$1 status
    local deadline=$((SECONDS + BUILD_TIMEOUT))

    while (( SECONDS < deadline )); do
        status=$(openstack server show "$name" -f value -c status 2>/dev/null || echo MISSING)
        echo "$name status=$status"
        if [[ $status == ACTIVE ]]; then
            return 0
        fi
        if [[ $status == ERROR ]]; then
            openstack server show "$name" -f yaml -c fault || true
            return 1
        fi
        sleep 3
    done
    echo "$name did not become ACTIVE within ${BUILD_TIMEOUT}s" >&2
    return 1
}

wait_for_ssh() {
    local name=$1 ip=$2
    local deadline=$((SECONDS + SSH_TIMEOUT))

    while (( SECONDS < deadline )); do
        if ping -c 1 -W 1 "$ip" >/dev/null 2>&1 && nc -z -w2 "$ip" 22; then
            echo "$name SSH ready at $ip"
            return 0
        fi
        echo "Waiting for SSH to $name at $ip"
        sleep 3
    done
    echo "$name did not become reachable by SSH within ${SSH_TIMEOUT}s" >&2
    return 1
}

run_one() {
    local name=$1 flavor=$2
    local fip fip_id guest_script log

    echo "===== Creating $name with flavor $flavor ====="
    openstack server delete "$name" >/dev/null 2>&1 || true
    for _ in $(seq 1 30); do
        openstack server show "$name" >/dev/null 2>&1 || break
        sleep 2
    done

    openstack server create --image "$IMAGE" --flavor "$flavor" --network "$NETWORK" "$name"
    wait_for_active "$name"

    fip=$(openstack floating ip create "$PUBLIC_NETWORK" \
        --tag "$FLOATING_IP_TAG" \
        --description "pci-sim serial echo test for $name" \
        -f value -c floating_ip_address)
    fip_id=$(openstack floating ip show "$fip" -f value -c id)
    echo "Associating floating IP $fip ($fip_id) to $name"
    openstack server add floating ip "$name" "$fip"

    wait_for_ssh "$name" "$fip"

    guest_script=$(mktemp)
    log=$(mktemp "/tmp/${name}.serial-echo.XXXXXX.log")
    write_guest_probe "$guest_script"
    ssh_guest_probe "$name" "$fip" "$guest_script" "$log"
    rm -f "$guest_script"

    grep -q "SERIAL_ECHO_OK" "$log"
    grep -Eq "DEVICE=0x0003|DEVICE=0x1001|DEVICE=0x8250" "$log"
    echo "===== PASS $name (log: $log) ====="

    if [[ $KEEP -eq 0 ]]; then
        echo "Cleaning up $name and floating IP $fip"
        openstack server delete "$name" >/dev/null 2>&1 || true
        for _ in $(seq 1 60); do
            openstack server show "$name" >/dev/null 2>&1 || break
            sleep 2
        done
        openstack floating ip delete "$fip_id" >/dev/null 2>&1 || true
    else
        echo "Keeping $name and floating IP $fip"
    fi
}

require_command openstack
require_command python3
require_command ssh
require_command nc
require_command ping
require_openstack_auth

if [[ $CLEANUP_ONLY -eq 1 ]]; then
    cleanup_resources
    exit 0
fi

open_default_security_group

if [[ $RUN_NOVA -eq 1 ]]; then
    run_one "$NOVA_SERVER" "$NOVA_FLAVOR"
fi
if [[ $RUN_CYBORG -eq 1 ]]; then
    run_one "$CYBORG_SERVER" "$CYBORG_FLAVOR"
fi

echo "All requested pci-sim serial echo tests passed."
