#!/bin/bash
# plugin.sh - devstack plugin for cyborg

# devstack plugin contract defined at:
# https://docs.openstack.org/devstack/latest/plugins.html

echo_summary "cyborg devstack plugin.sh called: $1/$2"
source $DEST/cyborg/devstack/lib/cyborg

case $1 in
    "stack")
        case $2 in
            "pre-install")
                clone_cyborg_client
                ;;
            "install")
                echo_summary "Installing Cyborg"
                install_cyborg
                install_cyborg_client
                ;;
            "post-config")
                # stack/post-config - Called after the layer 0 and 2 services
                # have been configured. All configuration files for enabled
                # services should exist at this point.
                echo_summary "Configuring Cyborg"
                configure_cyborg
                create_cyborg_accounts
                ;;
            "extra")
                # stack/extra - Called near the end after layer 1 and 2
                # services have been started.
                # Initialize cyborg
                init_cyborg
                # Start the cyborg API and cyborg taskmgr components
                echo_summary "Starting Cyborg"
                start_cyborg
                ;;
        esac
        ;;
    "unstack")
        # unstack - Called by unstack.sh before other services are shut down.
        stop_cyborg
        ;;
    "clean")
        # clean - Called by clean.sh before other services are cleaned, but after
        # unstack.sh has been called.
        cleanup_cyborg
        ;;
esac
