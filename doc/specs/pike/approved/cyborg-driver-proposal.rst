..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==============================
Cyborg Generic Driver Proposal
==============================

https://blueprints.launchpad.net/openstack-cyborg/+spec/generic-driver-cyborg

This spec proposes to provide the initial design for Cyborg's generic driver.

Problem description
===================

This blueprint proposes to add a generic driver for openstack-cyborg.
The goal is to provide users & operators with a reliable generic
implementation that is hardware agnostic and provides basic
accelerator functionality.

Use Cases
---------

* As an admin user and a non-admin user with elevated privileges, I should be
  able to identify and discover attached accelerator backends.
* As an admin user and a non-admin user with elevated privileges, I should be
  able to view services on each attached backend after the agent has
  discovered services on each backend.
* As an admin user and a non-admin user, I should be able to list and update
  attached accelerators by driver by querying nova with the Cyborg-API.
* As an admin user and a non-admin user with elevated privileges, I should be
  able to install accelerator generic driver.
* As an admin user and a non-admin user with elevated privileges, I should be
  able to uninstall accelerator generic driver.
* As an admin user and a non-admin user with elevated privileges, I should be
  able to issue attach command to the instance via the driver which gets
  routed to Nova via the Cyborg API.
* As an admin user and a non-admin user with elevated privileges, I should be
  able to issue detach command to the instance via the driver which gets
  routed to Nova via the Cyborg API.

Proposed change
===============

* Cyborg needs a reference implementation that can be used as a model for
  future driver implementations and that will be referred to as the generic
  driver implementation
* Develop the generic driver implementation that supports CRUD operations for
  accelerators for single backend and multi backend setup scenarios.


Alternatives
------------

None

Data model impact
-----------------

* The generic driver will update the central database when any CRUD or
  attach/detach operations take place

REST API impact
---------------

This blueprint proposes to add the following APIs:
*cyborg install-driver <driver_id>
*cyborg uninstall-driver <driver_id>
*cyborg attach-instance <instance_id>
*cyborg detach-instance <instance_id>
*cyborg service-list
*cyborg driver-list
*cyborg update-driver <driver_id>
*cyborg discover-services

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

None

Performance Impact
------------------

None

Other deployer impact
---------------------

None

Developer impact
----------------

Developers will have access to a reference generic implementation which
can be used to build vendor-specific drivers.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Rushil Chugh <rushil.chugh@gmail.com>

Work Items
----------

This change would entail the following:
* Add a feature to identify and discover attached accelerator backends.
* Add a feature to list services running on the backend
* Add a feature to attach accelerators to the generic backend.
* Add a feature to detach accelerators from the generic backend.
* Add a feature to list accelerators attached to the generic backend.
* Add a feature to modify accelerators attached to the generic backend.
* Defining a reference implementation detailing the flow of requests between
  the cyborg-api, cyborg-conductor and nova-compute services.

Dependencies
============

Dependent on Cyborg API and Agent implementations.

Testing
=======

* Unit tests will be added test Cyborg generic driver.

Documentation Impact
====================

None

References
==========

None

History
=======


.. list-table:: Revisions
   :header-rows: 1

   * - Release
     - Description
   * - Pike
     - Introduced
