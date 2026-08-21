:title: Driver Development Guide

Driver Development Guide
########################

This document covers the process for developing a new Cyborg accelerator
driver.

Overview
========

Cyborg manages hardware accelerators (FPGAs, GPUs, NICs, SSDs, AI chips)
through a pluggable driver architecture. Each driver implements device
discovery, resource reporting to Placement, and device-specific operations
such as programming or binding.

See :doc:`/contributor/repo-overview` for repository structure and
:doc:`/admin/support-matrix` for the current driver support status.

Before You Start
================

``Environment Setup:``
  Set up a development environment using DevStack. See
  :doc:`/contributor/devstack_setup` for detailed instructions.

``Review Existing Drivers:``
  Study the drivers in ``cyborg/accelerator/drivers/`` to understand common
  patterns. The ``fake`` and ``pci`` drivers are good starting points.

``Example Driver Guides:``
  * :doc:`/contributor/nvme-driver`: NVMe driver development environment setup
  * :doc:`/contributor/intel-nic-sriov`: Intel NIC driver with SR-IOV
    configuration

``Understand the Placement Integration:``
  Drivers report inventory to Placement and must follow the resource
  class and trait conventions documented in the admin guide.

Driver Development Process
==========================

.. note::

   This process documents the complete workflow for developing a new driver.

1. ``Derive a Driver Class``

   ``cyborg/accelerator/drivers/driver.py`` will be the base class of all
   drivers in the future, but the details of which methods should be
   implemented may change.

   Note that currently, some existing drivers do not inherit from
   the correct class.

2. ``Register the Driver``

   Add an entry point in ``pyproject.toml``:

   .. code-block:: toml

     [project.entry-points."cyborg.accelerator.driver"]
     new_accel_driver = "cyborg.accelerator.drivers.newtype.driver:NewAcceleratorDriver"

3. ``Add Configuration Options``

   Define driver-specific config in ``cyborg/conf/``. Follow the pattern used
   by existing drivers.

4. ``Implement Resource Reporting``

   Ensure your driver reports appropriate resource classes and traits to
   Placement. Coordinate with the conductor for inventory updates.

5. ``Write Tests``

   Add unit tests in ``cyborg/tests/unit/accelerator/drivers/`` and functional
   tests if applicable. Mock hardware interactions to avoid CI dependencies.

6. ``Document Configuration``

   Add a section to ``doc/source/configuration/drivers.rst`` explaining how
   operators enable and configure your driver.

7. ``Update Support Matrix``

   Add your driver to :doc:`/admin/support-matrix` with testing status and
   supported products.

Next Steps
==========

See :doc:`/contributor/devstack_setup` for running Cyborg locally and
:doc:`/contributor/tempest-testing` for integration test coverage.
