==============================
DevStack Setup for Development
==============================

Overview
========

This guide provides instructions for setting up a development environment for
Cyborg using DevStack. DevStack is a set of scripts used to quickly bring up
a complete OpenStack environment for development and testing purposes.

This guide covers the basic DevStack setup with the Cyborg plugin enabled.
For advanced driver configuration and device testing, refer to the
driver-specific documentation.

Download DevStack
=================

Clone the DevStack repository:

.. code-block:: console

   $ git clone https://opendev.org/openstack/devstack
   $ cd devstack

The ``devstack`` repo contains a script that installs OpenStack.

Create stack user (optional)
============================

DevStack should be run as a non-root user with sudo enabled (standard logins to
cloud images such as "ubuntu" or "cloud-user" are usually fine).

.. note::

   Skip this step if you already have a user with passwordless sudo privileges.

You can create a separate stack user to run DevStack with using the
provided script. This will clone the current devstack code locally, then setup
the "stack" account that devstack services will run under. Finally, it will
move devstack into its default location in /opt/stack/devstack:

.. code-block:: console

   $ sudo ./tools/create-stack-user.sh
   $ cd ../..
   $ sudo mv devstack /opt/stack
   $ sudo chown -R stack:stack /opt/stack/devstack

Then switch to the stack user:

.. code-block:: console

   $ sudo su - stack
   $ cd /opt/stack/devstack

Configure local.conf
====================

Create a ``local.conf`` file at the root of the devstack git repo. You can
use the sample configuration template provided in the Cyborg repository as
a starting point.

.. code-block:: console

   $ cp <cyborg-repo>/devstack/local-conf local.conf

The minimal configuration required to enable Cyborg is:

.. code-block:: ini

   [[local|localrc]]
   enable_plugin cyborg https://opendev.org/openstack/cyborg

The sample ``local.conf`` file in the Cyborg repository includes additional
optional configurations such as service management, logging settings, and
host tuning options for memory-constrained environments.

Edit the ``local.conf`` file as needed for your environment, particularly
the password settings and host IP configuration.

Run DevStack
============

.. code-block:: console

   $ ./stack.sh

Verify Cyborg Services
======================

After DevStack completes successfully, check for openstack accelerator devices:

.. code-block:: console

   $ source openrc admin admin
   $ openstack accelerator device list

You can view Cyborg service logs using journalctl:

.. code-block:: console

   $ journalctl -u devstack@cyborg-api
   $ journalctl -u devstack@cyborg-cond
   $ journalctl -u devstack@cyborg-agent

Managing Cyborg Services
========================

During development, you may need to restart Cyborg services after making
code changes:

.. code-block:: console

   $ sudo systemctl restart devstack@cyborg-api
   $ sudo systemctl restart devstack@cyborg-cond
   $ sudo systemctl restart devstack@cyborg-agent

Multi-Node Lab
==============

If you want to set up OpenStack with Cyborg in a realistic test configuration
with multiple physical servers, please refer to [#MultiNodeLab]_.

Controller node
---------------

On the controller node, disable the Cyborg agent service:

.. code-block:: ini

   [[local|localrc]]
   disable_service cyborg-agent

Compute Nodes
-------------

On compute nodes, enable the Cyborg agent and disable API and conductor
services:

.. code-block:: ini

   [[local|localrc]]
   enable_service cyborg-agent
   disable_service cyborg-api
   disable_service cyborg-cond

- If you do not want to run cyborg-agent on the controller, you can disable it.
- You do not need to enable cyborg-api and cyborg-cond on compute nodes.

Testing with unmerged changes
=============================

To test with changes that have not been merged, the enable_plugin
line can be modified to specify the branch/reference to be cloned.

.. code-block:: ini

   enable_plugin cyborg https://review.opendev.org/openstack/cyborg refs/changes/28/708728/1

The format is:

.. code-block:: ini

   enable_plugin <directory name> <git repo url> <change/revision>

Cell V2 Deployment
==================

Compute node services must be mapped to a cell before they can be used.
For Cell V2 deployment, please refer to [#CellV2]_.

References
==========

.. [#MultiNodeLab] `OpenStack Multi-Node Lab Setup
   <https://docs.openstack.org/devstack/latest/guides/multinode-lab.html>`_
.. [#CellV2] `OpenStack Cell V2 Deployment Guide
   <https://docs.openstack.org/nova/latest/user/cells.html>`_
