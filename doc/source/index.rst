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
---------------------------

The documentation in this section is aimed at Cloud
Operators needing to install or configure Cyborg.

Installation
~~~~~~~~~~~~

The detailed install guide for Cyborg.

.. toctree::
   :maxdepth: 1

   install/index
   admin/config-wsgi

Configuration Reference
~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   configuration/index
   reference/support-matrix

Maintenance
~~~~~~~~~~~

Once you are running cyborg, the following information is extremely useful.

* :doc:`Admin Guide </admin/index>`: A collection of guides for administrating
  cyborg.

.. # NOTE(amotoki): toctree needs to be placed at the end of the secion to
   # keep the document structure in the PDF doc.
.. toctree::
   :hidden:

   admin/index

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

* :doc:`/contributor/rest_api_version_history`: The Cyborg API evolves over
  time through Microversions. This provides the history of all those changes.
  Consider it a "what's new" in the Cyborg API.

Documentation for Developers
----------------------------

.. toctree::
   :maxdepth: 1

   contributor/index
   contributor/rest_api_version_history

Indices and tables
==================

* :ref:`search`
