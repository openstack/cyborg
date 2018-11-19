#!/bin/bash
# plugin.sh - devstack plugin for cyborg

# devstack plugin contract defined at:
# https://docs.openstack.org/devstack/latest/plugins.html

echo_summary "cyborg devstack plugin.sh called: $1/$2"
source $DEST/cyborg/devstack/lib/cyborg
source $DEST/cyborg/devstack/lib/opae

if is_service_enabled cyborg-api cyborg-cond; then
    if [[ "$1" == "stack" ]]; then
        if [[ "$2" == "pre-install" ]]; then
        # stack/pre-install - Called after (OS) setup is complete and before
        # project source is installed
            echo_summary "Installing additional Cyborg packages"
            if install_opae_packages; then
               echo_summary "INFO: Additional Cyborg packages installed"
            else
               echo "WARNING: Failed to install additional Cyborg packages"
            fi
        elif [[ "$2" == "install" ]]; then
        # stack/install - Called after the layer 1 and 2 projects source and
        # their dependencies have been installed
            echo_summary "Installing Cyborg"
            if ! is_service_enabled nova; then
                source $RC_DIR/lib/nova_plugins/functions-libvirt
                install_libvirt
            fi
            install_cyborg
        elif [[ "$2" == "post-config" ]]; then
        # stack/post-config - Called after the layer 1 and 2 services have been
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
        uninstall_opae_packages
    fi
fi
