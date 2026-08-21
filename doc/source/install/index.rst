==================
Installation Guide
==================

This guide covers installing Cyborg, the OpenStack Acceleration Service, from
source or packages. The instructions are written for manual installation but
are also designed to help packagers and deployment automation tools understand
the component dependencies, configuration requirements, and service ordering.

Overview
========

Cyborg manages hardware accelerators (FPGAs, GPUs, NICs, SSDs, AI chips) in
OpenStack clouds. A typical deployment includes:

``cyborg-api``
    REST API service, normally deployed behind a WSGI server (Apache/nginx +
    uwsgi). Handles device profile queries, ARQ creation, and accelerator
    discovery.

``cyborg-conductor``
    Central orchestration service. Manages placement inventory updates,
    coordinates device bindings, and interacts with Nova for instance
    lifecycle events.

``cyborg-agent``
    Runs on compute nodes. Discovers local accelerators via drivers, reports
    inventory to the conductor, and manages device programming and attachment.

Cyborg integrates with **Nova** (instance lifecycle), **Placement** (resource
inventory and scheduling), **Neutron** (for SmartNIC flows), and **Glance**
(for FPGA bitstream metadata).

Prerequisites
=============

Before installing Cyborg:

* An operational OpenStack deployment with at least ``Keystone`` and
  ``Placement``. (``Neutron`` and ``Glance`` would be required later
  when creating resources that interact with those services).
  Cyborg is tested against the current and previous OpenStack
  release.
* A database (MySQL/MariaDB).
* A message broker (RabbitMQ recommended).
* Python 3.11 or newer.

See the :doc:`/admin/support-matrix` for supported VM operations and driver
compatibility with specific Nova versions.

Installation Methods
====================

.. toctree::
   :maxdepth: 1

   install-from-source
   install-from-pip

Both methods share common configuration steps documented in :doc:`common`.

Post-Installation
=================

After installing Cyborg services:

``Configuration``
    See :doc:`common` for database setup, service credentials, API endpoints,
    and ``cyborg.conf`` settings. Driver-specific configuration is covered in
    :doc:`/configuration/index`.

``Upgrades``
    See :doc:`/admin/upgrade` for safe upgrade procedures, database migration
    ordering, and online data migration requirements. Always review
    release-specific notes before upgrading.

``Security``
    See :doc:`/admin/security` for ARQ ownership scoping, service token
    requirements for Nova integration, and Keystone configuration. Cyborg
    requires service tokens for operations on bound ARQs.

``Verification``
    After starting services, verify Cyborg is operational:

    .. code-block:: console

        $ openstack accelerator device list
        $ cyborg-status upgrade check

    The :doc:`/cli/cyborg-status` command performs health and upgrade
    readiness checks.

Next Steps
==========

* ``Driver Configuration``: See :doc:`/configuration/drivers` to enable and
  configure accelerator drivers for your hardware.
* ``DevStack Development``: For development environments, see
  :doc:`/contributor/devstack_setup`.
* ``User Guide``: End users should consult :doc:`/user/using-cyborg` for
  creating device profiles and requesting accelerators in instances.
* ``Admin Guide``: Operators should review :doc:`/admin/index` for placement
  integration, coexistence with PCI whitelists, and ARQ lifecycle management.

Related Documentation
=====================

* :doc:`/admin/index` — Administration guide
* :doc:`/configuration/index` — Configuration reference
* :doc:`/admin/support-matrix` — Supported operations and drivers
* :doc:`/cli/index` — Command-line tools reference
