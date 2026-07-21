# plugin.sh - devstack plugin for cyborg

# devstack plugin contract defined at:
# https://docs.openstack.org/devstack/latest/plugins.html

echo_summary "cyborg devstack plugin.sh called: $1/$2"
CYBORG_DEVSTACK_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$CYBORG_DEVSTACK_DIR/lib/cyborg"
source "$CYBORG_DEVSTACK_DIR/lib/pci_sim"

case "$1" in
    "stack")
        case "$2" in
            "pre-install")
                clone_cyborg_client
                ;;
            "install")
                echo_summary "Installing Cyborg"
                install_cyborg
                install_cyborg_client
                if [[ "$ENABLE_PCI_SIM" == True ]]; then
                    install_package pciutils
                    if [[ "$PCI_SIM_BUILD" == True ]]; then
                        async_runfunc build_pci_sim
                    fi
                fi
                ;;
            "post-config")
                # stack/post-config - Called after the layer 0 and 2 services
                # have been configured. All configuration files for enabled
                # services should exist at this point.
                echo_summary "Configuring Cyborg"
                configure_cyborg
                create_cyborg_accounts
                if [[ "$ENABLE_PCI_SIM" == True ]]; then
                    if [[ "$PCI_SIM_BUILD" == True ]]; then
                        async_wait build_pci_sim
                    fi
                    if [[ "$PCI_SIM_LOAD" == True ]]; then
                        load_pci_sim
                        configure_pci_sim_vfs
                        configure_pci_sim_nova_service_config
                    fi
                fi
                ;;
            "extra")
                # stack/extra - Called near the end after layer 1 and 2
                # services have been started.
                # Configure pci-sim Cyborg service settings before starting
                # the agent so it picks up pci_driver and passthrough_whitelist.
                if [[ "$ENABLE_PCI_SIM" == True && \
                    "$PCI_SIM_LOAD" == True ]]; then
                    configure_pci_sim_cyborg_service_config
                fi
                # Initialize cyborg
                init_cyborg
                # Start the cyborg API and cyborg taskmgr components
                echo_summary "Starting Cyborg"
                start_cyborg
                ;;
            "test-config")
                # stack/test-config - Called at the end of devstack used to configure tempest
                # or any other test environments
                if is_service_enabled tempest; then
                    echo_summary "Configuring Tempest for Cyborg needs"
                    cyborg_configure_tempest
                fi
                if [[ "$ENABLE_PCI_SIM" == True ]]; then
                    create_pci_sim_test_resources
                fi
                ;;
        esac
        ;;
    "unstack")
        # unstack - Called by unstack.sh before other services are shut down.
        stop_cyborg
        if [[ "$ENABLE_PCI_SIM" == True ]]; then
            unload_pci_sim || true
        fi
        ;;
    "clean")
        # clean - Called by clean.sh before other services are cleaned, but after
        # unstack.sh has been called.
        cleanup_cyborg
        if [[ "$ENABLE_PCI_SIM" == True ]]; then
            unload_pci_sim || true
        fi
        ;;
esac
