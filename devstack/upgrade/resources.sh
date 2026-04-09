#!/usr/bin/env bash

set -o errexit

source $GRENADE_DIR/grenaderc
source $GRENADE_DIR/functions

TOP_DIR=${TOP_DIR:-$TARGET_DEVSTACK_DIR}

source $TOP_DIR/openrc admin admin

set -o xtrace

# Device profile groups JSON requesting one fake FPGA device
DEVICE_PROFILE_GROUPS='[{"resources:FPGA": "1", "trait:CUSTOM_FAKE_DEVICE": "required"}]'

# Create a device profile that requests one FPGA from the fake driver
function create_device_profile {
    local dp_uuid
    dp_uuid=$(openstack accelerator device profile create \
        cyborg-grenade-dp "$DEVICE_PROFILE_GROUPS" -f value -c uuid)
    resource_save cyborg dp_uuid "$dp_uuid"
}

# Verify the pre-upgrade device profile is still listable after upgrade
function verify_device_profile {
    local dp_uuid=$(resource_get cyborg dp_uuid)
    openstack accelerator device profile show "$dp_uuid"
}

# Create a new device profile post-upgrade to confirm new resources work.
# If it already exists (e.g. previous run didn't reach destroy), use its uuid.
function create_post_upgrade_device_profile {
    local dp_uuid
    dp_uuid=$(openstack accelerator device profile list -f value -c uuid -c name \
        2>/dev/null | awk -v name="cyborg-grenade-post-dp" '$2==name {print $1; exit}')
    if [[ -z "$dp_uuid" ]]; then
        dp_uuid=$(openstack accelerator device profile create \
            cyborg-grenade-post-dp "$DEVICE_PROFILE_GROUPS" -f value -c uuid)
    fi
    resource_save cyborg post_dp_uuid "$dp_uuid"
}

# Verify the post-upgrade device profile is listable
function verify_post_upgrade_device_profile {
    local dp_uuid=$(resource_get cyborg post_dp_uuid)
    openstack accelerator device profile show "$dp_uuid"
}

# Remove the pre-upgrade device profile
function delete_device_profile {
    local dp_uuid=$(resource_get cyborg dp_uuid)
    openstack accelerator device profile delete "$dp_uuid"
}

# Remove the post-upgrade device profile
function delete_post_upgrade_device_profile {
    local dp_uuid=$(resource_get cyborg post_dp_uuid)
    openstack accelerator device profile delete "$dp_uuid"
}

# Currently no good way to verify without the API
function verify_noapi {
    :
}

# Create cyborg resources before upgrade
function create {
    create_device_profile
}

# Verify pre-upgrade resources survive, then create and verify new ones
function verify {
    verify_device_profile
    create_post_upgrade_device_profile
    verify_post_upgrade_device_profile
}

# Clean up all cyborg resources in reverse order
function destroy {
    delete_post_upgrade_device_profile
    delete_device_profile
}

# Dispatcher
case $1 in
    "create")
        create
        ;;
    "verify_noapi")
        verify_noapi
        ;;
    "verify")
        verify
        ;;
    "destroy")
        destroy
        ;;
    "force_destroy")
        set +o errexit
        destroy
        ;;
esac
