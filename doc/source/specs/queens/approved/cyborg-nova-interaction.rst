..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=======================
Cyborg-Nova interaction
=======================

https://blueprints.launchpad.net/cyborg/+spec/cyborg-nova-interaction

Cyborg, as a service for managing accelerators of any kind needs to cooperate
with Nova on two planes: Cyborg should be able to inform Nova about the
resources through placement API[1], so that scheduler can leverage user
requests for particular functionality into assignment of specific resource
using resource provider which possess an accelerator, and second, Cyborg should
be able to provide information on how Nova compute can attach particular
resource to VM.

In a nutshell, this blueprint will define how information between Nova and
Cyborg will be exchanged.

Problem description
===================

Currently in OpenStack the use of non-standard accelerator hardware is
supported in that features exist across many of the core servers that allow
these resources to be allocated, passed through, and eventually used.

What remains a challenge though is the lack of an integrated workflow; there
is no way to configure many of the accelerator features without significant
by hand effort and service disruptions that go against the goals of having
a easy, stable, and flexible cloud.

Cyborg exists to bring these disjoint efforts together into a more standard
workflow. While many components of this workflow already exist, some don't
and will need to be written expressly for this goal.

Use Cases
---------

All possible use cases were briefly described in backlog Nova spec [2]. It
might be distinguished two main use case groups for which accelerators might be
used:

* Accelerator might be attached to the VM, where workload demands acceleration.
  That can be achieved by passing whole PCI device, certain host device from
  ``/dev/`` filesystem, passing Virtual Function, etc.
* Accelerator might be utilized by infrastructure, like accelerating virtual
  switches (i.e. Open vSwitch), and than utilized via appropriate service (like
  Neutron for example).


Proposed Workflow
=================

Using a method not relevant to this proposal Cyborg Agent inspects hardware
and finds accelerators that it is interested in setting up for use.

These accelerators are registered into the Cyborg Database and the Cyborg
Conductor is now responsible for using the Nova placement API to create
corresponding traits and resources.

One of the primary responsibilities of the Cyborg conductor is to keep the
placement API in sync with reality. For example if here is a device with
a virtual function or a FPGA with a given program Cyborg may be tasked with
changing the virtual function on the NIC or the program on the FPGA. At which
point the previously specified traits and resources need to be updated.
Likewise Cyborg will be watching monitoring Nova's instances to ensure that
doing this doesn't pull resources out from under an allocated instance.

At a high level what we need to be able to do is the following

1. Add a PCI device to Nova's whitelist live
   (config only / needs implementation)
2. Add information about this device to the placement API
   (existing / being worked)
3. Hotplug and unplug PCI devices from instances
   (existing / not sure how well maintained)


Alternatives
------------

Don't use Cyborg, struggle with bouncing services and grub config changes
yourself.

Data model impact
-----------------

N/A

REST API impact
---------------

N/A

Security impact
---------------

N/A

Notifications impact
--------------------

N/A

Other end user impact
---------------------

N/A

Performance Impact
------------------

N/A

Other deployer impact
---------------------

N/A

Developer impact
----------------

N/A

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  None

Work Items
----------

* Implementation of Cyborg service
* Implementation of Cyborg agent
* Blueprint for changes in Nova
* Implementation of the POC which exposes functionality and interoperability
  between Cyborg and Nova

Dependencies
============

This design depends on the changes which may or may not be accepted in Nova
project. Other than that is ongoing work on Nested resource providers:
https://specs.openstack.org/openstack/nova-specs/specs/ocata/approved/nested-resource-providers.html
Which would be an essential feature in Placement API, which will be leveraged
by Cyborg.


Testing
=======

There would be a need to provide another gate, which would provide an
accelerator for tests.

Documentation Impact
====================

* Document new nova api for whitelisting
* Document developer and user interaction with the workflow
* Document placement api standard identifiers

References
==========

* [1] https://docs.openstack.org/developer/nova/placement.html
* [2] https://review.openstack.org/#/c/318047/
* [3] https://github.com/openstack/nova/blob/390c7e420f3880a352c3934b9331774f7afdadcc/nova/compute/resource_tracker.py#L751


History
=======

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Queens
     - Introduced
