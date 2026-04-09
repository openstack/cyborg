#!/usr/bin/env bash

# ``upgrade-cyborg``

echo "*********************************************************************"
echo "Begin $0"
echo "*********************************************************************"

# Clean up any resources that may be in use
cleanup() {
    set +o errexit

    echo "********************************************************************"
    echo "ERROR: Abort $0"
    echo "********************************************************************"

    # Kill ourselves to signal any calling process
    trap 2; kill -2 $$
}

trap cleanup SIGHUP SIGINT SIGTERM

# Keep track of the grenade directory
RUN_DIR=$(cd $(dirname "$0") && pwd)

# Source params
source $GRENADE_DIR/grenaderc

# Import common functions
source $GRENADE_DIR/functions

# This script exits on an error so that errors don't compound and you see
# only the first error that occurred.
set -o errexit

# Upgrade cyborg
# ==============

# Get functions from current DevStack
source $TARGET_DEVSTACK_DIR/stackrc
source $TARGET_DEVSTACK_DIR/lib/apache
source $TARGET_DEVSTACK_DIR/lib/tls
source $TARGET_DEVSTACK_DIR/lib/keystone
source $TARGET_DEVSTACK_DIR/lib/placement

TOP_DIR=${TOP_DIR:-$TARGET_DEVSTACK_DIR}

source $TOP_DIR/openrc admin admin

CYBORG_DEVSTACK_DIR=$(dirname $(dirname $0))
source $CYBORG_DEVSTACK_DIR/settings
source $CYBORG_DEVSTACK_DIR/lib/cyborg

# Print the commands being run so that we can see the command that triggers
# an error.  It is also useful for following allowing as the install occurs.
set -o xtrace

# Save current config files for posterity
[[ -d $SAVE_DIR/etc.cyborg ]] || cp -pr $CYBORG_CONF_DIR $SAVE_DIR/etc.cyborg

# Install the target upgrade
install_cyborg

# calls upgrade-cyborg for specific release
upgrade_project cyborg $RUN_DIR $BASE_DEVSTACK_BRANCH $TARGET_DEVSTACK_BRANCH

# Make sure it is OK to do an upgrade. We aren't parsing the output of this
# command because the output could change based on the checks it makes.
$CYBORG_BIN_DIR/cyborg-status upgrade check && ret_val=$? || ret_val=$?
if [ $ret_val -gt 1 ] ; then
    # Warnings are permissible and returned as status code 1, errors are
    # returned as greater than 1 which means there is a major upgrade
    # stopping issue which needs to be addressed.
    echo "WARNING: Status check failed, we're going to attempt to apply the schema update and then re-evaluate."
    $CYBORG_BIN_DIR/cyborg-dbsync --config-file=$CYBORG_CONF_FILE upgrade
    $CYBORG_BIN_DIR/cyborg-status upgrade check && ret_val=$? || ret_val=$?
    if [ $ret_val -gt 1 ] ; then
        die $LINENO "Cyborg DB Status check failed, returned: $ret_val"
    fi
fi

$CYBORG_BIN_DIR/cyborg-dbsync --config-file=$CYBORG_CONF_FILE upgrade || die $LINENO "DB migration error"

# When using uWSGI: create config if missing; re-enable Apache site (stop_cyborg
# disables it, and we only call write_uwsgi_config when conf is missing).
if [[ "$CYBORG_USE_UWSGI" == "True" ]]; then
    if [[ ! -f "$CYBORG_UWSGI_CONF" ]]; then
        write_uwsgi_config "$CYBORG_UWSGI_CONF" "$CYBORG_UWSGI" "/accelerator"
        endpoints=$(openstack endpoint list --service cyborg -c ID -f value)
        for id in $endpoints; do
            openstack endpoint delete $id
        done
        create_cyborg_accounts
    fi
    enable_apache_site cyborg-api
    restart_apache_server
fi

start_cyborg

# Don't succeed unless the services come up
ensure_services_started cyborg-api cyborg-cond cyborg-agent

set +o xtrace
echo "*********************************************************************"
echo "SUCCESS: End $0"
echo "*********************************************************************"

