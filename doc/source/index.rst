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

All end user (and some administrative) features of Cyborg are exposed via a
REST API, which can be used to build more complicated logic or automation with
Cyborg. This can be consumed directly, or via various SDKs. The Cyborg API
has experienced an evolution from V1 API to V2 API. Cyborg introduced and
landed a totally `new DB modeling schema
<https://specs.openstack.org/openstack/cyborg-specs/specs/stein/approved/cyborg-database-model-proposal.html>`_.
for tracking cyborg resources in Stein release. The legacy v1 api does not
match the new data model, which we changed pretty much. So cyborg introduced
version 2.0 APIs and deprecated V1 APIs in Train release. Then in the Ussuri
release, V1 APIs are removed, and full V2 APIs and microversion are supported.
The following resource may help you get started with V2 APIs directly.

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
