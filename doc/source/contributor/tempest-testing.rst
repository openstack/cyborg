===================================
Running Cyborg Tempest Plugin Tests
===================================

Overview
========

This guide provides instructions for setting up and running Cyborg tempest
plugin tests in a development environment. Tempest is the OpenStack
integration test suite, and the Cyborg tempest plugin contains integration
tests specifically for the Cyborg service.

The Cyborg tempest plugin is maintained in a separate repository at
`opendev.org/openstack/cyborg-tempest-plugin
<https://opendev.org/openstack/cyborg-tempest-plugin>`_.

Prerequisites
=============

Before running Cyborg tempest tests, ensure you have:

* A working DevStack environment with Cyborg enabled
  (see :doc:`/contributor/devstack_setup`)
* Cyborg services running (cyborg-api, cyborg-conductor, cyborg-agent)
* At least one accelerator device configured (real hardware or emulated devices
  or fake driver)

For setting up emulated NVMe devices for testing, see
:doc:`/contributor/nvme-driver`.

Installing Tempest and Cyborg Plugin
=====================================

Install Tempest
---------------

If tempest is not already installed in your DevStack environment, you can
enable it by adding the following to your ``local.conf`` before running
``stack.sh``:

.. code-block:: ini

   [[local|localrc]]
   enable_service tempest

Install Cyborg Tempest Plugin
------------------------------

Clone and install the Cyborg tempest plugin:

.. code-block:: console

   $ cd /opt/stack
   $ git clone https://opendev.org/openstack/cyborg-tempest-plugin
   $ cd cyborg-tempest-plugin
   $ source /opt/stack/tempest/.tox/tempest/bin/activate
   $ pip install -e .

The plugin will be automatically discovered by tempest through the
``tempest.test_plugins`` entry point.

Configure Cyborg Service
-------------------------

Edit the ``etc/tempest.conf`` file to enable Cyborg tests:

.. code-block:: ini

   [service_available]
   cyborg = True

If you're using DevStack with the Cyborg plugin enabled, these settings are
automatically configured by the ``cyborg_configure_tempest`` function in
``devstack/lib/cyborg``.

Running Tempest Tests
=====================

List Cyborg tempest plugin
----------------------------

To see Cyborg tempest plugin discovered by tempest:

.. code-block:: console

   $ cd /opt/stack/tempest
   $ tempest list-plugins

This shows all installed tempest plugins, including cyborg_tempest_plugin.


Run All Cyborg Tests
---------------------

To run all Cyborg tempest tests, navigate to the tempest directory, activate
the tempest virtual environment, then run:

.. code-block:: console

   $ cd /opt/stack/tempest
   $ source .tox/tempest/bin/activate
   $ tempest run --regex cyborg_tempest_plugin

The ``--regex`` flag filters tests by their module path. For example, to run
only the API tests:

.. code-block:: console

   $ tempest run --regex cyborg_tempest_plugin.tests.api

For more options such as running a specific test class or a single test method,
see the `Tempest documentation <https://docs.openstack.org/tempest/latest/>`_.

Detailed Test Logs
------------------

Detailed test logs are stored in the /opt/stack/tempest directory:

.. code-block:: console

   $ cd /opt/stack/tempest
   $ cat tempest.log

The ``tempest.log`` file contains detailed logs for all test executions,
including API requests/responses and service logs.

Check Cyborg Service Logs
--------------------------

If tests fail, check the Cyborg service logs:

.. code-block:: console

   $ sudo journalctl -u devstack@cyborg-api -f
   $ sudo journalctl -u devstack@cyborg-conductor -f
   $ sudo journalctl -u devstack@cyborg-agent -f

Verify Device Discovery
------------------------

Ensure that Cyborg has discovered accelerator devices:

.. code-block:: console

   $ export OS_CLOUD=devstack-admin
   $ openstack accelerator device list

If no devices are listed, review the device configuration in
:doc:`/contributor/nvme-driver` or your hardware-specific driver documentation.


Adding New Tests
----------------

To add new tempest tests for Cyborg:

1. Clone the cyborg-tempest-plugin repository:

   .. code-block:: console

      $ git clone https://opendev.org/openstack/cyborg-tempest-plugin
      $ cd cyborg-tempest-plugin

2. Create a new test file in the appropriate directory:

   * ``cyborg_tempest_plugin/tests/api/`` - For API tests
   * ``cyborg_tempest_plugin/tests/scenario/`` - For scenario tests

3. Follow the existing test patterns and tempest best practices

4. Run the new tests locally to ensure they pass

5. Submit the changes to Gerrit for review

References
==========

* `Cyborg Tempest Plugin Repository
  <https://opendev.org/openstack/cyborg-tempest-plugin>`_
* `Tempest Documentation <https://docs.openstack.org/tempest/latest/>`_
* `OpenStack Testing Guidelines
  <https://docs.openstack.org/project-team-guide/project-setup/testing.html>`_
* :doc:`/contributor/devstack_setup` - DevStack setup guide
* :doc:`/contributor/nvme-driver` - NVMe driver configuration
