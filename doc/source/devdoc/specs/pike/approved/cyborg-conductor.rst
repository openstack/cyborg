..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
     Cyborg Conductor Proposal
==========================================

https://blueprints.launchpad.net/openstack-cyborg/+spec/cyborg-agent

This spec proposes the responsibilities and initial design of the
Cyborg Conductor.

Problem description
===================

Cyborg requires a conductor on the controller hosts to manage the cyborg
system state and coalesce database operations.

Use Cases
---------

Use of accelerators attached to virtual machine instances in OpenStack

Proposed change
===============

Cyborg Conductor will reside on the control node and will be
responsible for stateful actions taken by Cyborg. Acting as both a cache to
the database and as a method of combining reads and writes to the database.
All other Cyborg components will go through the conductor for database operations.

Alternatives
------------

Having each Cyborg Agent instance hit the database on it's own is a possible
alternative, and it may even be feasible if the accelerator load monitoring rate is
very low and the vast majority of operations are reads. But since we intend to store
metadata about accelerator usage updated regularly this model probably will not scale
well.

Data model impact
-----------------

Using the conductor 'properly' will result in little or no per instance state and stateful
operations moving through the conductor with the exception of some local caching where it
can be garunteed to work well.

REST API impact
---------------

N/A

Security impact
---------------

Negligible

Notifications impact
--------------------

N/A

Other end user impact
---------------------

Faster Cybrog operation and less database load.

Performance Impact
------------------

Generally positive so long as we don't overload the messaging bus trying
to pass things to the Conductor to write out.

Other deployer impact
---------------------

Conductor must be installed and configured on the controllers.


Developer impact
----------------

None for API users, internally heavy use of message passing will
be required if we want to keep all system state in the controllers.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  jkilpatr

Other contributors:
  None

Work Items
----------

* Implementation
* Integration with API and Agent

Dependencies
============

* Cyborg API spec
* Cyborg Agent spec

Testing
=======

This component should be possible to fully test using unit tests and functional
CI using the dummy driver.

Documentation Impact
====================

Some configuration values tuning save out rate and other parameters on the controller
will need to be documented for end users

References
==========

Cyborg API Spec
Cyborg Agent Spec

History
=======


.. list-table:: Revisions
   :header-rows: 1

   * - Release
     - Description
   * - Pike
     - Introduced
