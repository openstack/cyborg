#!/usr/bin/env bash

set -o errexit

source $GRENADE_DIR/grenaderc
source $GRENADE_DIR/functions

# We need base DevStack functions for this
source $BASE_DEVSTACK_DIR/functions
source $BASE_DEVSTACK_DIR/stackrc # needed for status directory
source $BASE_DEVSTACK_DIR/lib/tls
source $BASE_DEVSTACK_DIR/lib/apache

CYBORG_DEVSTACK_DIR=$(dirname $(dirname $0))
source $CYBORG_DEVSTACK_DIR/settings
source $CYBORG_DEVSTACK_DIR/plugin.sh
source $CYBORG_DEVSTACK_DIR/lib/cyborg

set -o xtrace

stop_cyborg

# sanity check that service is actually down
ensure_services_stopped cyborg-api cyborg-cond cyborg-agent
