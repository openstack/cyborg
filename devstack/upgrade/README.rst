=============================
Upgrade Testing using grenade
=============================

Run a Grenade upgrade: deploy a base DevStack, then upgrade to a target
release and verify Cyborg device profiles survive the upgrade.

Requirements
============

- 8 GB RAM, 8 vCPUs (or reduce services in the configs).

Setup
=====

1. Clone Grenade::

     git clone https://opendev.org/openstack/grenade

2. Configure Grenade. Use Grenade's base configuration files with minimal
   Cyborg-specific overrides.

   a. **Create localrc** with Cyborg-specific branch settings::

        cat > localrc <<EOF
        # Set base release branch (update to match desired base release)
        BASE_DEVSTACK_BRANCH=stable/2025.2
        TARGET_DEVSTACK_BRANCH=master
        EOF

   b. **Create pluginrc** to enable Cyborg grenade plugin::

        cat > pluginrc <<EOF
        enable_grenade_plugin cyborg https://opendev.org/openstack/cyborg
        EOF

3. (Optional) Customize devstack configs for resource-constrained environments.

   Edit ``devstack.local.conf.base`` and ``devstack.local.conf.target`` to
   disable unneeded services::

     [[local|localrc]]
     disable_service s-account s-container s-object s-proxy
     disable_service etcd
     disable_service c-api c-bak c-sch c-vol cinder
     disable_service horizon

Run
===

From the Grenade repo root::

     cd grenade
     ./grenade.sh

Clean up after test failure::

     ./clean.sh
     ./grenade.sh

Configuration Details
=====================

**Required Files** (in Grenade repo root):

- ``localrc`` — Grenade variables (branches, paths). Minimum requirement:
  set ``BASE_DEVSTACK_BRANCH`` to the release you want to upgrade from.

- ``pluginrc`` — Enables the Cyborg grenade plugin.

**Optional Files** (customize as needed):

- ``devstack.local.conf.base`` — Base (old) release DevStack configuration.
- ``devstack.local.conf.target`` — Target (new) release DevStack configuration.

**Cyborg Grenade Plugin** (``cyborg/devstack/upgrade/``):

Automatically used by Grenade when the plugin is enabled in ``pluginrc``:

- ``resources.sh`` — Create/verify/destroy device profiles during upgrade.
- ``shutdown.sh`` — Stop Cyborg services before upgrade.
- ``upgrade.sh`` — Install target Cyborg, run DB migrations, start services.
- ``settings`` — Register Cyborg project/DB with Grenade.

Configuration Examples
=======================

**Minimal localrc**::

  BASE_DEVSTACK_BRANCH=stable/2025.2
  TARGET_DEVSTACK_BRANCH=master

**Reduce resource usage** (add to devstack.local.conf files)::

  disable_service s-account s-container s-object s-proxy etcd cinder horizon

**Custom passwords** (add to devstack.local.conf files)::

  ADMIN_PASSWORD=password
  DATABASE_PASSWORD=password
  MYSQL_PASSWORD=password
  RABBIT_PASSWORD=password
  SERVICE_PASSWORD=password

**Tuning for CI/stability**::

  ENABLE_SYSCTL_MEM_TUNING="True"
  ENABLE_SYSCTL_NET_TUNING="True"
  ENABLE_ZSWAP="True"

**Fixed network range for tenant networks**::

  NETWORK_GATEWAY=10.0.0.1
  FIXED_RANGE=10.0.0.0/22

Notes
=====

- Grenade provides default settings for passwords, networking, paths, and
  service configurations. Only override settings specific to your test
  environment.

- The ``BASE_DEVSTACK_BRANCH`` should match the OpenStack release you want
  to upgrade from (e.g., stable/2025.2, stable/2026.1).

- Grenade automatically detects the Cyborg upgrade plugin when
  ``devstack_plugins`` includes Cyborg in CI jobs. For local testing,
  use ``pluginrc`` to enable the plugin.

- In CI job, use `grenade_devstack_localrc` var to pass extra things
  in devstack localrc on the base or target node::

      grenade_devstack_localrc:
        old:
           <setting for base devstack localrc>
        new:
           <setting for target devstack localrc>
        shared:
           <setting which are applicable for both base and target>
