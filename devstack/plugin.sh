#!/bin/bash
# plugin.sh - devstack plugin for cyborg

# devstack plugin contract defined at:
# https://docs.openstack.org/devstack/latest/plugins.html

echo_summary "cyborg devstack plugin.sh called: $1/$2"
source $DEST/cyborg/devstack/lib/cyborg
source $DEST/cyborg/devstack/lib/opae


if is_service_enabled cyborg-api cyborg-cond || is_service_enabled cyborg-agent; then
    if [[ "$1" == "stack" ]]; then
        if [[ "$2" == "pre-install" ]]; then
            pre_install_agent
        elif [[ "$2" == "install" ]]; then
            echo_summary "Installing Cyborg"
            install_agent
            install_cyborg
        elif [[ "$2" == "post-config" ]]; then
        # stack/post-config - Called after the layer 0 and 2 services have been
        # configured. All configuration files for enabled services should exist
        # at this point.
            echo_summary "Configuring Cyborg"
            configure_cyborg
            create_cyborg_accounts
        elif [[ "$2" == "extra" ]]; then
        # stack/extra - Called near the end after layer 1 and 2 services have
        # been started.
            # Initialize cyborg
            init_cyborg

            # Start the cyborg API and cyborg taskmgr components
            echo_summary "Starting Cyborg"
            start_cyborg
        fi
    fi

    if [[ "$1" == "unstack" ]]; then
    # unstack - Called by unstack.sh before other services are shut down.
        stop_cyborg
    fi

    if [[ "$1" == "clean" ]]; then
    # clean - Called by clean.sh before other services are cleaned, but after
    # unstack.sh has been called.
        cleanup_cyborg
        cleanup_agent
    fi
fi
