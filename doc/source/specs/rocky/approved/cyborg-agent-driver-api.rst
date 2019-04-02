..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
Cyborg Agent-Driver API
==========================================

Cyborg agent interacts with each Cyborg driver in the compute node to
discover available devices. This spec defines how the agent-driver API
is structured.

No change is proposed to the way the agent discovers the drivers on
start or restart.

This spec is common to all accelerators, including GPUs, High Precision
Time Synhronization (HPTS) cards, etc. Since FPGAs have more aspects to
be considered than other devices, some sections may focus on FPGA-specific
factors. The spec calls out the FPGA-specific aspects.

The scope of this spec is Rocky release, but the API has been designed
to be extensible for future releases. Accordingly, the spec calls out
the Rocky-specific aspects.

Problem description
===================

The [#Cyborg_Nova_scheduling_spec]_ specifies that devices are
represented using Resource Providers (RPs), Resource Classes (RCs)
and traits. The information needed to create them has to come from
the Cyborg driver to the Cyborg agent, which in turn needs to
push it to the Cyborg Conductor.

The main challenge is discovering the device topology for FPGAs.
An FPGA may have one or more Partial Reconfiguration regions,
and those regions may have one or more accelerators nested inside them.
Further, it may have local memory that is either partitioned or
shared among the regions.

Use Cases
---------

* Devices of different types (GPUs, FPGAs, HPTS cards, Quick Assist) are
  present in the same host.

* FPGAs of different types, possibly from different vendors, are present
  in the same host.

* An FPGA may have one or more regions. Each region may have one
  or more accelerators.

  * In Rocky, we may support only one region per FPGA, and only one
    accelerator per region.

* For Rocky, it is proposed that local memory need not be exposed as
  a resource to orchestration. That is because, since there is only
  one region per FPGA, an instance attached to that region will be
  able to access all the memory, no matter how much there is. For
  non-FPGA devices like GPUs, there does not seem to be a requirement
  to expose video RAM.

Cyborg will assume and handle the following component relationships:

* One product (e.g. Intel PAC Arria 10) may correspond to multiple
  PCI vendor/device IDs.

* One PCI vendor/device ID may correspond to different region type IDs.
  This could be either because there are multiple regions in the same device
  or because there are different versions/revisions of the same device.

* But the same region type ID will never show up in products with
  different PCI IDs.

Proposed change
===============

Today, the Cyborg agent invokes the discover() API for each driver
that it finds. The discover() API returns a dictionary indexed by
the PCI BDF of a device. The value element in the key-value pair of
the dictionary contains the components and characteristics
of the device with that BDF.

We propose to retain the same model, but enhance the dictionary to
include enough information to create the resource providers and traits
needed to populate Placement. Here are the additional proposed keys
in the device dictionary for each PF:

|   ``"type": <enum-string>`` # One of GPU, FPGA, etc.
|   ``"vendor": <string>``
|   ``"product": <string>``

Also, in the ``regions`` entry for each PF, it is proposed to add
the following keys:

|   ``"region-type-uuid": <uuid>``  # Optional, default: NULL
|   ``"bitstream-id": <uuid>`` # Glance/other UUID, optional, default: NULL
|   ``"function-uuid": <uuid>`` # Optional, default: NULL

When the agent receives this dictionary for a device, it will do
the following:

* If there is nested RP support, create an RP for the device and each
  region within.

* Create a device type trait: ``CUSTOM_<type>_<vendor>_<product>``.
  Apply it to the device RP (if nRP support exists) or the compute node RP.

  * E.g. CUSTOM_FPGA_INTEL_PAC_ARRIA10.

  * NOTE: The agent will convert all characters to upper case, replace
    spaces with underscores, and check for conformance to custom trait
    syntax (see [#Custom_traits]_)

* Create region type traits for each region, of the form:
  ``CUSTOM_<type>_<vendor>_REGION_<type-uuid>``. Apply them to the
  corresponding region RP (if nRP support exists) or the compute node RP.

  * E.g. CUSTOM_FPGA_INTEL_REGION_<type-uuid>

  * NOTE: For UUIDs, the agent will convert all hexadecimal digits to upper
    case, replace hyphens with underscores and validate all characters.

* Create function type traits for each function in each region, of the form:
  ``CUSTOM_<type>_<vendor>_FUNCTION_<function-uuid>``. Apply them to the
  corresponding region RP (if nRP support exists) or the compute node RP.

  * E.g. CUSTOM_FPGA_INTEL_FUNCTION_<function-uuid>

Alternatives
------------

N/A

Data model impact
-----------------

Add the new fields to the database under Deployables and Attributes.

REST API impact
---------------

None

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

None

Implementation
==============

Assignee(s)
-----------

None

Work Items
----------

Dependencies
============

None

Testing
=======

Need to update unit tests to check for the newly added fields.

Documentation Impact
====================

None

References
==========

.. [#Cyborg_Nova_scheduling_spec] `Cyborg/Nova Scheduling spec <https://review.openstack.org/#/c/554717>`_

.. [#Custom_traits] `Custom Traits <https://specs.openstack.org/openstack/nova-specs/specs/pike/implemented/resource-provider-traits.html#rest-api-impact>`_

History
=======

Optional section intended to be used each time the spec is updated to describe
new design, API or any database schema updated. Useful to let reader
understand what's happened along the time.

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Rocky
     - Introduced
