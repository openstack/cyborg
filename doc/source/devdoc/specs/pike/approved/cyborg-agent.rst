..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
     Cyborg Agent Proposal
==========================================

https://blueprints.launchpad.net/openstack-cyborg/+spec/cyborg-agent

This spec proposes the responsibilities and initial design of the
Cyborg Agent.

Problem description
===================

Cyborg requires an agent on the compute hosts to manage the several
responsibilities, including locating accelerators, monitoring their
status, and orchestrating driver operations.

Use Cases
---------

Use of accelerators attached to virtual machine instances in OpenStack

Proposed change
===============

Cyborg Agent resides on various compute hosts and monitors them for accelerators.
On it's first run Cyborg Agent will run the detect accelerator functions of all
it's installed drivers. The resulting list of accelerators available on the host
will be reported to the conductor where it will be stored into the database and
listed during API requests. By default accelerators will be inserted into the
database in a inactive state. It will be up to the operators to manually set
an accelerator to 'ready' at which point cyborg agent will be responsible for
calling the drivers install function and ensuring that the accelerator is ready
for use.

In order to mirror the current Nova model of using the placement API each Agent
will send updates on it's resources directly to the placement API endpoint as well
as to the conductor for usage aggregation. This should keep placement API up to date
on accelerators and their usage.

Alternatives
------------

There are lots of alternate ways to lay out the communication between the Agent
and the API endpoint or the driver. Almost all of them involving exactly where we
draw the line between the driver, Conductor , and Agent. I've written my proposal
with the goal of having the Agent act mostly as a monitoring tool, reporting to
the cloud operator or other Cyborg components to take action. A more active role
for Cyborg Agent is possible but either requires significant synchronization with
the Conductor or potentially steps on the toes of operators.

Data model impact
-----------------

Cyborg Agent will create new entries in the database for accelerators it detects
it will also update those entries with the current status of the accelerator
at a high level. More temporary data like the current usage of a given accelerator
will be broadcast via a message passing system and won't be stored.

Cyborg Agent will retain a local cache of this data with the goal of not losing accelerator
state on system interruption or loss of connection.


REST API impact
---------------

TODO once we firm up who's responsible for what.

Security impact
---------------

Monitoring capability might be useful to an attacker, but without root
this is a fairly minor concern.

Notifications impact
--------------------

Notifying users that their accelerators are ready?

Other end user impact
---------------------

Interaction details around adding/removing/setting up accelerators
details TBD.

Performance Impact
------------------

Agent heartbeat for updated accelerator performance stats might make
scaling to many accelerator hosts a challenge for the Cyborg endpoint
and database. Perhaps we should consider doing an active 'load census'
before scheduling instances? But that just moves the problem from constant
load to issues with a bootstorm.


Other deployer impact
---------------------

By not placing the drivers with the Agent we keep the deployment footprint
pretty small. We do add development complexity and security concerns sending
them over the wire though.

Developer impact
----------------

TBD

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  <jkilpatr>

Other contributors:
  <launchpad-id or None>

Work Items
----------

* Agent implementation

Dependencies
============

* Cyborg Driver Spec
* Cyborg API Spec
* Cyborg Conductor Spec

Testing
=======

CI infrastructure with a set of accelerators, drivers, and hardware will be
required for testing the Agent installation and operation regularly.

Documentation Impact
====================

Little to none. Perhaps on an on compute config file that may need to be
documented. But I think it's best to avoid local configuration where possible.

References
==========

Other Cyborg Specs

History
=======


.. list-table:: Revisions
   :header-rows: 1

   * - Release
     - Description
   * - Pike
     - Introduced
