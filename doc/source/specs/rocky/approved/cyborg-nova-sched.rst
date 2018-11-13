..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
Cyborg-Nova Interaction for Scheduling
==========================================

https://blueprints.launchpad.net/cyborg/+spec/cyborg-nova-interaction

Cyborg provides a general management framework for accelerators, such
as FPGAs, GPUs, etc. For scheduling an instance that needs accelerators,
Cyborg needs to work with Nova on three levels:

* Representation and Discovery: Cyborg shall represent accelerators as
  resources in Placement. When a device is discovered, Cyborg updates
  resource providers, inventories, traits, etc. in Placement.

* Instance placement/scheduling: Cyborg may provide a filter and/or weigher
  that limit or prioritize hosts based on available accelerator resources,
  but it is expected that Placement itself can handle most requirements.

* Attaching accelerators to instances. In the compute node, Cyborg shall
  define a workflow based on interacting with Nova through a new os-acc
  library (similar to os-vif and os-brick).

This spec addresses the first two aspects. There is another spec to
address the attachment of accelerators to instances [#os-acc]_.
Cyborg also needs to handle some aspects for FPGAs without involving
Nova, specifically FPGA programming and bitstream management. They
will be covered in other specs. This spec is independent of those specs.

This spec is common to all accelerators, including GPUs, High Precision
Time Synchronization (HPTS) cards, etc. Since FPGAs have more aspects to
be considered than other devices, some sections may focus on FPGA-specific
factors. The spec calls out the FPGA-specific aspects.

Smart NICs based on FPGAs fall into two categories: those which expose
the FPGA explicitly to the host, and those that do not. Cyborg's scope
includes the former. This spec includes such devices, though the
Cyborg-Neutron interaction is out of scope.

The scope of this spec is Rocky release.

Terminology
===========
* Accelerator: The unit that can be assigned to an instance for
  offloading specific functionality. For non-FPGA devices, it is either the
  device itself or a virtualized version of it (e.g. vGPUs). For FPGAs, an
  accelerator is either the entire device, a region within the device or a
  function.

* Bitstream: An FPGA image, usually a binary file, possibly with
  vendor-specific metadata. A bitstream may implement one or more functions.

* Function: A specific functionality, such as matrix multiplication or video
  transcoding, usually represented as a string or UUID. This term may be used
  with multi-function devices, including FPGAs and other fixed function
  hardware like Intel QuickAssist.

* Region: A part of the FPGA which can be programmed without disrupting
  other parts of that FPGA. If an FPGA does not support Partial
  Reconfiguration, the entire device constitutes one region. A region
  may implement one or more functions.

Here is an example diagram for an FPGA with multiple regions, and multiple
functions in a region::

         PCI A     PCI B
          |        |
  +-------|--------|-------------------+
  |       |        |                   |
  |  +----|--------|---+   +--------+  |
  |  | +--|--+ +---|-+ |   |        |  |
  |  | | Fn A| | Fn B| |   |        |  |
  |  | +-----+ +-----+ |   |        |  |
  |  +-----------------+   +--------+  |
  |  Region 1              Region 2    |
  |                                    |
  +------------------------------------+

Problem description
===================
Cyborg's representation and handling of accelerators needs to be consistent
with Nova's Placement API. Specifically, they must be modeled in terms of
Resource Providers (RPs), Resource Classes (RCs) and Traits.

Though PCI Express is entrenched in the data center, some accelerators
may be exposed to the host via some other protocol. Even with PCI, the
connections between accelerator components and PCI functions
may vary across devices. Accordingly, Cyborg should not represent
accelerators as PCI functions.

For instances that need accelerators, we need to define a way for Cyborg
to be included seamlessly in the Nova scheduling workflow.

Use Cases
---------
We need to satisfy the following use cases for the tenant role:

* Device as a Service (DaaS): The flavor asks for a device.

  * FPGA variation: The flavor asks for a device to which specific
    bitstream(s) can be applied. There are three variations, the first
    two of which delegate bitstream programming to Cyborg for secure
    programming:

    * Request-time Programming: The flavor specifies a bitstream. (Cyborg
      applies the bitstream before instance bringup. This is similar to
      AWS flow.)

    * Run-time Programming: The instance may request one or more
      bitstreams dynamically. (Cyborg receives the request and does
      the programming.)

    * Direct Programming: The instance directly programs the FPGA
      region assigned to it, without delegating it to Cyborg. The
      security questions that this raises need to be addressed in
      the future. (This is listed only for completeness; this is not
      going to be addressed in Rocky, or even future releases till
      the security concerns are fully addressed.)

* Accelerated Function as a Service (AFaaS): The flavor asks for a
  function (e.g. ipsec) attached to the instance. The operator may
  satisfy this use case in two ways:

  * Pre-programmed: Do not allow orchestration to modify any function,
    for any of these reasons:

    * Only fixed function hardware is available. (E.g. ASICs.)

    * Operational simplicity.

    * Assure tenants of programming security, by doing all programming offline
      through some audited process.

  * For FPGAs, allow orchestration to program as needed, to maximize
    flexibility and availability of resources.

An operator must be able to provide both Device as a Service and Accelerated
Function as a Service in the same cluster, to serve all
kinds of users: those who are device-agnostic, those using 3rd party
bitstreams, and those using their own bitstreams (incl. developers).

The goal for Cyborg is to provide the mechanisms to enable all these use
cases.

In this spec, we do not consider bitstream developer or device developer
roles. Also, we assume that each accelerator device is dedicated to a
compute node, rather than shared among several nodes.

Proposed change
===============

Representation
--------------

  * Cyborg will represent a generic accelerator for a device type as a
    custom Resource Class (RC) for that type, of the form
    CUSTOM_ACCELERATOR_<device-type>. E.g. CUSTOM_ACCELERATOR_GPU,
    CUSTOM_ACCELERATOR_FPGA, etc. This helps in defining separate quotas
    for different device types.

  * Device-local memory is the memory available to the device alone,
    usually in the form of DDR, QDR or High Bandwidth Memory in the
    PCIe board along with the device. It can also be represented as an
    RC of the form CUSTOM_ACCELERATOR_MEMORY_<memory-type>. E.g.
    CUSTOM_ACCELERATOR_MEMORY_DDR. A single PCIe board may have more
    than one type of memory.

  * In addition, each device/region is represented as a Resource Provider
    (RP). This enables traits to be applied to it and other RPs/RCs to
    be contained within it. So, a device RP provides one or more instances
    of that device type's RC. This depends on nested RP support in
    Nova [#nRP]_.

       * For FPGAs, both the device and the regions within it will be
         represented as RPs. This allows the hierarchy within an FPGA
         to be naturally modelled as an RP hierarchy.

       * Using Nested RPs is the preferred way. But, until Nova
         supports nested RPs, Cyborg shall associate the
         RCs and traits (described below) with the compute node RPs. This
         requires that all devices on a single host must share the same
         traits. If nested RP support becomes usable after Rocky release,
         the operator needs to handle the upgrade as below:

         * Terminate all instances using accelerators.

         * Remove all Cyborg traits and inventory on all compute node RPs,
           perhaps by running a script.

         * Perform the Cyborg upgrade. Post-upgrade, the new agent/driver(s)
           will create RPs for the devices and publish the traits
           and inventory.

  * Cyborg will associate a Device Type trait with each device, of the
    form CUSTOM_<device-type>-<vendor>. E.g. CUSTOM_GPU_AMD or
    CUSTOM_FPGA_XILINX. This trait is intended to help match the
    software drivers/libraries in the instance image. This is meant to
    be used in a flavor when a single driver/library in the instance
    image can handle most or all of device types from a vendor.

       * For FPGAs, this trait and others will be applied to the region
         RPs which are children of the device RPs as well.

  * Cyborg will associate a Device Family trait with each device as
    needed, of the form CUSTOM_<device-type>_<vendor>_<family>.
    E.g. CUSTOM_FPGA_INTEL_ARRIA10.
    This is not a product name, but the name of a device family, used to
    match software in the instance image with the device family. This is
    a refinement of the Device Type Trait. It is meant to be used in
    a flavor when there are different drivers/libraries for different
    device families. Since it may be tough to forecast whether a new
    device family will need a new driver/library, it may make sense to
    associate both these traits with the same device RP.

  * For FPGAs, Cyborg will associate a region type trait with each region
    (or with the FPGA itself if there is no Partial Reconfiguration
    support), of the form CUSTOM_FPGA_REGION_<vendor>__<uuid>.
    E.g.  CUSTOM_FPGA_REGION_INTEL_<uuid>. This is needed for Device as a
    Service with FPGAs.

  * For FPGAs, Cyborg may associate a function type trait with a region
    when the region gets programmed, of the form
    CUSTOM_FPGA_FUNCTION_<vendor>_<uuid>. E.g.
    CUSTOM_FPGA_FUNCTION_INTEL_<gzip-uuid>.
    This is needed for AFaaS use case. This is updated when Cyborg
    reprograms a region as part of AFaaS request.

  * For FPGAs, Cyborg should associate a CUSTOM_PROGRAMMABLE trait with
    every region. This is needed to lay the groundwork for
    multi-function accelerators in the future. Flavors should ask for
    this trait, except in the pre-programmed case.

  * For FPGAs, since they may implement a wide variety of functionality,
    we may also attach a Functionality Trait.
    E.g. CUSTOM_FPGA_COMPUTE, CUSTOM_FPGA_NETWORK, CUSTOM_FPGA_STORAGE.

  * The Cyborg agent needs to get enough information from the Cyborg driver
    to create the RPs, RCs and traits. In particular, it needs to get the
    device type string, region IDs and function IDs from the driver. This
    requires the driver/agent interface to be enhanced [#drv-api]_.

  * The modeling in Placement represents generic virtual accelerators as
    resource classes, and devices/regions as RPs. This is PCI-agnostic.
    However, many FPGA implementations use PCI Express in general, and
    SR-IOV in particular. In those cases, it is expected that Cyborg will
    pass PCI VFs to instances via PCI Passthrough, and retain the PCI PF
    in the host for management.

Flavors
-------
  For the sake of illustrating how the device representation in Nova
  can be used, and for completeness, we now show how to define flavors
  for various use cases. Please see [#flavor]_ for more details.

  * A flavor that needs device access always asks for one or more instances
    of 'resource:CUSTOM_ACCELERATOR_<device-type>'. In addition, it
    needs to specify the right traits.

  * Example flavor for DaaS:

    | ``resources:CUSTOM_ACCELERATOR_HPTS=1``
    | ``trait:CUSTOM_HPTS_ZTE=required``

    NOTE: For FPGAs, the flavor should also include CUSTOM_PROGRAMMABLE trait.

  * Example flavor for AFaaS Pre-programed:

    | ``resources:CUSTOM_ACCELERATOR_FPGA=1``
    | ``trait:CUSTOM_FPGA_INTEL_ARRIA10=required``
    | ``trait:CUSTOM_FPGA_FUNCTION_INTEL_<gzip-uuid>=required``

  * Example flavor for AFaaS Orchestration-Programmed:

    | ``resources:CUSTOM_ACCELERATOR_FPGA=1``
    | ``trait:CUSTOM_FPGA_INTEL_ARRIA10=required``
    | ``trait:CUSTOM_PROGRAMMABLE=required``
    | ``function:CUSTOM_FPGA_FUNCTION_INTEL_<gzip-uuid>=required``
      (Not interpreted by Nova.)

    * NOTE: When Nova supports preferred traits, we can use that instead
      of 'function' keyword in extra specs.

    * NOTE: For Cyborg to fetch the bitstream for this function, it
      is assumed that the operator has configured the function UUID
      as a property of the bitstream image in Glance.

  * Another example flavor for AFaaS Orchestration-Programmed which
    refers to a function by name instead of UUID for ease of use:

    | ``resources:CUSTOM_ACCELERATOR_FPGA=1``
    | ``trait:CUSTOM_FPGA_INTEL_ARRIA10=required``
    | ``trait:CUSTOM_PROGRAMMABLE=required``
    | ``function_name:<string>=required``
      (Not interpreted by Nova.)

    * NOTE: This assumes the operator has configured the function name
      as a property of the bitstream image in Glance. The FPGA
      hardware is not expected to expose function names, and so
      Cyborg will not represent function names as traits.

  * A flavor may ask for other RCs, such as local memory.

  * A flavor may ask for multiple accelerators, using the granular resource
    request syntax. Cyborg can tie function and bitstream fields in
    the extra_specs to resources/traits using an extension of the granular
    resource request syntax (see References) which is not interpreted by Nova.

    | ``resourcesN: CUSTOM_ACCELERATOR_FPGA=1``
    | ``traitsN: CUSTOM_FPGA_INTEL_ARRIA10=required``
    | ``othersN: function:CUSTOM_FPGA_FUNCTION_INTEL_<gzip-uuid>=required``

Scheduling workflow
--------------------
We now look at the scheduling flow when each device implements only
one function. Devices with multiple functions are outside the scope for now.

  * A request spec with a flavor comes to Nova conductor/scheduler.

  * Placement API returns the list of RPs which contain the requested
    resources with matching traits. (With nested RP support, the returned
    RPs are device/region RPs. Without it, they are compute node RPs.)

  * FPGA-specific: For AFaaS orchestration-programmed use case, Placement
    will return matching devices but they may not have the requested
    function. So, Cyborg may provide a weigher which checks the
    allocation candidates to see which ones have the required function trait,
    and ranks them higher. This requires no change to Cyborg DB.

  * The request_spec goes to compute node (ignoring Cells for now).

    NOTE: When one device/region implements multiple functions and
    orchestration-driven programming is desired, the inventory of that
    device needs to be adjusted.
    This can be addressed later and is not a priority for Rocky release.
    See References.

  * Nova compute calls os-acc/Cyborg [#os-acc]_.

  * FPGA-specific: If the request spec asks for a function X in extra specs,
    but X is not present in the selected region RP, Cyborg should program
    that region.

  * Cyborg should associate RPs/RCs and PFs/VFs with Deployables in its
    internal DB. It can use such mappings associating the requested resource
    (device/function) with some attach handle that can be used to
    attach the resource to an instance (such as a PCI function).

NOTE : This flow is PCI-agnostic: no PCI whitelists involved.

Handling Multiple Functions Per Device
--------------------------------------

Alternatives
------------

N/A

Data model impact
-----------------

Following changes are needed in Cyborg.

* Do not publish PCI functions as resources in Nova. Instead, publish
  RC/RP info to Nova, and keep RP-PCI mapping internally.

* Cyborg should associate RPs/RCs and PFs/VFs with Deployables in its
  internal DB.

* Driver/agent interface needs to report device/region types so that
  RCs can be created.

* Deployables table should track which RP corresponds to each Deployable.

REST API impact
---------------

None

Security impact
---------------

This change allows tenants to initiate FPGA bitstream programming. To mitigate
the security impact, it is proposed that only 2 methods are offered for
programming (flavor asks for a bitstream, or the running instance asks for
specific bitstreams) and both are handled through Cyborg. There is no direct
access from an instance to an FPGA.

Notifications impact
--------------------

None

Other end user impact
---------------------

None

Performance Impact
------------------

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

* Decide specific changes needed in Cyborg conductor, db, agent and drivers.

Dependencies
============

* `Nested Resource Providers
  <https://specs.openstack.org/openstack/nova-specs/specs/rocky/approved/nested-resource-providers-allocation-candidates.html>`_

* `Nova Granular Requests
  <https://specs.openstack.org/openstack/nova-specs/specs/rocky/approved/granular-resource-requests.html>`_

NOTE: the granular requests feature is needed to define a flavor that requests
non-identical accelerators, but is not needed for Cyborg development in Rocky.

Testing
=======

For each vendor driver supported in this release, we need to integrate the
corresponding FPGA type(s) in the CI infrastructure.

Documentation Impact
====================

None

References
==========

.. [#os-acc] `Specification for Compute Node <https://review.openstack.org/#/c/566798/>`_

.. [#nRP] `Nested RPs in Rocky <https://specs.openstack.org/openstack/nova-specs/specs/rocky/approved/nested-resource-providers-allocation-candidates.html>`_

.. [#drv-api] `Specification for Cyborg Agent-Driver API <https://review.openstack.org/#/c/561849/>`_

.. [#flavor] `Custom Resource Classes in Flavors <https://specs.openstack.org/openstack/nova-specs/specs/pike/implemented/custom-resource-classes-in-flavors.html>`_

.. [#qspec] `Cyborg Nova Queens Spec <https://github.com/openstack/cyborg/blob/master/doc/specs/queens/approved/cyborg-nova-interaction.rst>`_

.. [#ptg] `Rocky PTG Etherpad for Cyborg Nova Interaction <https://etherpad.openstack.org/p/cyborg-ptg-rocky-nova-cyborg-interaction>`_

.. [#multifn] `Detailed Cyborg/Nova scheduling <https://etherpad.openstack.org/p/Cyborg-Nova-Multifunction>`_

.. [#mails] `Openstack-dev email discussion <https://lists.openstack.org/pipermail/openstack-dev/2018-April/128951.html>`_



History
=======

Optional section intended to be used each time the spec is updated to describe
new design, API or any database schema updated. Useful to let reader know
what happened over time.

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Rocky
     - Introduced
