OpenStack Accelerator (Cyborg)
==============================

Cyborg is a general management framework for accelerators


Overview
--------

.. toctree::
    :maxdepth: 1

    user/introduction
    user/architecture
    user/usage

Documentation for Operators
----------------------------

The documentation in this section is aimed at Cloud
Operators needing to install or configure Cyborg.

Installation
~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1

   install/install-from-pip
   install/install-from-source
   admin/config-wsgi

Configuration Reference
~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   configuration/index
   reference/support-matrix

For End Users
-------------

As an end user of Cyborg, you'll use Cyborg to create and
manage accelerators with either tools or the API directly.

Tools for using Cyborg
~~~~~~~~~~~~~~~~~~~~~~

Information on the commands available through Cyborg's Command Line
Interface (CLI) can be found in this section of documentation.

.. toctree::
   :maxdepth: 1

   cli/index

Using the API
~~~~~~~~~~~~~

Following the Ussuri release, every Cyborg deployment should have the
following endpoints:

/ - list of available versions

/v2 - the version 2 of the Acceleration API, it uses microversions

/v2.0 - same API as v2, except uses microversions

The follwoing guide concentrates on documenting the v2 API, please note that
the v2.0 is the first microversion of the v2 API and are also covered by this
guide.

* `Cyborg API Reference <https://docs.openstack.org/api-ref/accelerator/>`_:
  The complete reference for the accelerator API, including all methods and
  request / response parameters and their meaning.

.. # TODO(brinzhang): After completing the
   `Cyborg API v2 <https://specs.openstack.org/openstack/cyborg-specs/specs/ussuri/approved/cyborg-api.html>`_
   API, the "Cyborg API Microversion History <https://xxx>"" management
   document will be added, and it will also be added here.

Documentation for Developers
----------------------------

.. toctree::
   :maxdepth: 1

   contributor/contributing
   contributor/devstack_setup
   contributor/driver-development-guide

Indices and tables
==================

* :ref:`search`
