..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==============================================
Cyborg-Nova-Glance Interaction in Compute Node
==============================================

Cyborg is a service for managing accelerators, such as FPGAs, GPUs, etc. For
scheduling an instance that needs accelerators, Cyborg needs to work with Nova
at three levels:

* Representation and Discovery: Cyborg shall represent accelerators
  as resources in Placement. When a device is discovered, Cyborg
  updates resource inventories in Placement.

* Instance placement/scheduling: Cyborg may provide a weigher
  that prioritizes hosts based on available accelerator resources.

* Attaching accelerators to instances. In the compute node, Cyborg
  shall define a workflow based on interacting with Nova through a
  new os-acc library (like os-vif and os-brick).

The first two aspects are addressed in [#CyborgNovaSched]_. This spec
addresses the attachment of accelerators to instances, via os-acc. For
FPGAs, Cyborg also needs to interact with Glance for fetching bitstreams.
Some aspects of that are covered in [#BitstreamSpec]_. This spec will
address the interaction of Cyborg and Glance in the compute node.

This spec is common to all accelerators, including GPUs, High Precision
Time Synchronization (HPTS) cards, etc. Since FPGAs have more aspects
to be considered than other devices, some sections may focus on
FPGA-specific factors. The spec calls out the FPGA-specific aspects.

Smart NICs based on FPGAs fall into two categories: those which
expose the FPGA explicitly to the host, and those that do not.  Cyborg's
current scope includes the former. This spec includes such devices,
though the Cyborg-Neutron interaction is out of scope.

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
Once Nova has picked a compute node for placement of an instance that needs
accelerators, the following steps needs to happen:

* Nova compute on that node has to invoke Cyborg Agent for handling the needed
  accelerators. This needs to happen through a library, named os-acc, patterned
  after os-vif (Neutron) and os-brick (Cinder).

* Cyborg Agent may call Glance to fetch a bitstream, either by id or based on
  tags.

* Cyborg Agent may need to call into a Cyborg driver to program said bitstream.

* Cyborg Agent needs to call into a Cyborg driver to prepare a device and/or
  obtain an attach handle (e.g. PCI BDF) that can be attached to the instance.

* Cyborg Agent returns enough information to Nova compute via os-acc for the
  instance to be launched.

The behavior of each of these steps needs to be specified.

In addition, the OpenStack Compute API [#ServerConcepts]_ specifies the
operations that can be done on an instance. The behavior with respect to
accelerators must be defined for each of these operations. That in turn is
related to when Nova compute calls os-acc.

Use Cases
---------
Please see [#CyborgNovaSched]_. We intend to support FPGAaaS with
request time programming, and AFaaS (both pre-programmed and
orchestrator-programmed scenarios).

Cyborg will discover accelerator resources whenever the Cyborg agent starts up.
PCI hot plug can be supported past Rocky release.

Cyborg must support all instance operations mentioned in OpenStack Compute API
[#ServerConcepts]_ in Rocky, except booting off a snapshot and live migration.

Proposed change
===============

OpenStack Server API Behavior
-----------------------------
The OpenStack Compute API [#ServerConcepts]_ mentions the list of operations
that can be performed on an instance. Of these, some will not be supported by
Cyborg in Rocky. The list of supported operations (with
the intended behaviors) are as follows:

* When an instance is started, the accelerators requested by that instance’s
  flavor must be attached to the instance. On termination, those resources are
  released.

* When an instance is paused, suspended or locked, the accelerator resources
  are left intact, and not detached from the instance. So, when the instance is
  unpaused, resumed or unlocked, there is nothing to do.

* When an instance is shelved, the accelerator resources are detached. On an
  unshelve, it is expected that the build operation will go through the
  scheduler again, so it is equivalent to an instance start.

* When an instance is deleted, the accelerator resources are detached. On a
  restore, it is expected that the build operation will go through the
  scheduler again, so it is equivalent to an instance start.

* Reboot: The accelerator resources are left intact. It is up the instance
  software to rediscover attached resources.

* Rebuild: Prior to the instance image replacement, all device access must be
  quiesced, i.e., accesses to devices from that instance must be completed and
  further accesses must be prohibited. The mechanics of such quiescing are
  outside the scope of this document. With that precondition, accelerator
  resources are left attached to the instance during the rebuild.

* Resize (with change of flavor): It is equivalent to a termination followed by
  re-scheduling and restart. The accelerator resources are detached on
  termination, and re-attached on when the instance is scheduled again.

* Cold migration: It is equivalent to a termination followed by re-scheduling
  and restart. The accelerator resources are detached on termination, and
  re-attached on when the instance is scheduled again.

* Evacuate: This is a forcible rebuild by the administrator. As the semantics
  of evacuation are left open even without accelerators, Cyborg’s behavior is
  also left undefined.

* Set administrator password, trigger crash dump: These are supported and not
  no-ops for accelerators.

The following instance operations are not supported in this release:

* Booting off a snapshot: The snapshot may have been taken when the attached
  accelerators were in a particular state. When booting off a previous
  snapshot, the current configuration and state of accelerators may not match
  the snapshot. So, this is unsupported.

* Live migration: Until a mechanism is defined to migrate accelerator state
  along with the instance, this is unsupported.

os_acc Structure
----------------
Cyborg will develop a new library named os-acc. That library will offer the
APIs listed later in this section. Nova Compute calls these APIs if it sees
that the requested flavor refers to CUSTOM_ACCELERATOR resource class, except
for the initialize() call, which is called unconditionally. Nova Compute calls
these APIs asynchronously, as suggested below::

   with ThreadPoolExecutor(max_workers=1) as executor:
      future = executor.submit(os_acc.<api>, *args)
      # do other stuff
      try:
         data = future.result()
      except:
         # handle exceptions

The APIs of os-acc are as below:

* initialize()

  * Called once at start of day. Waits for Cyborg Agent to be ready to accept
    requests, i.e., all devices enumerated and traits published.

  * Returns None on success.

  * Throws ``CyborgAgentUnavailable`` exception if Cyborg Agent cannot be
    contacted.

* plug(instance_info, selected_rp, flavor_extra_specs)

  * Parameters are all read-only. Here are their descriptions:

    * instance_info: dictionary containing instance UUID, instance name,
      project/tenant ID and VM image UUID. The instance name is needed for
      better logging, the project/tenant ID may be passed to some accelerator
      policy engine in the future and the VM image UUID may be used to query
      Glance for metadata about accelerator requirements that may be stored
      with the VM image.

    * selected_rp: Information about the selected resource provider is
      passed as a dictionary.

    * flavor_extra_specs: the extra_specs field in the flavor, including
      resource classes, traits and other fields interpreted by Cyborg.

  * Called by Nova compute when an instance is started, unshelved, or
    restored and after a resize or cold migration.

  * Called before an instance is built, i.e., before the specification of
    the instance is created. For libvirt-based hypervisors, this means
    the call happens before the instance’s domain XML is created.

  * As part of this call, Cyborg Agent may fetch bitstreams from Glance and
    initiate programming. It may fetch the bitstream specified in the
    request’s flavor extra specs, if any. If the request refers to a
    function ID/name, Cyborg Agent would query Glance to find bitstreams
    that provide the flavor and match the chosen device, and would then
    fetch the needed bitstream.

  * As part of this call, Cyborg Agent will locate the Deployable corresponding
    to the chosen RP, locate the attach handles (e.g. PCI BDF) needed, update
    its internal data structures in a persistent way, and return the needed
    information back to Nova.

  * Returns an array, with one entry per requested accelerator, each entry
    being a dictionary. The dictionary is structured as below for Rocky:

   | { “pci_id”: <pci bdf> }

* unplug(instance_info)

  * Parameters are all read-only. Here are their descriptions:

    * instance_info: dictionary containing instance UUID and instance
      name. The instance name is needed for better logging.

   * Called when an instance is stopped, shelved, or deleted and before
     a resize or cold migration.

   * As part of this call, Cyborg Agent will clean up internal resources, call
     the appropriate Cyborg driver to clean up the device resources and update
     its data structures persistently.

   * Returns the number of accelerators that were released. Errors may cause
     exceptions to be thrown.

Workflows
---------
The pseudocode for each os-acc API can be expressed as below::

  def initialize():
    # checks that all devices are discovered and their traits published
    # waits if any discovery operation is ongoing
    return None

  def plug(instance_info, rp, extra_specs):
    validate_params(....)
    glance = glanceclient.Client(...)
    driver = # select Cyborg driver for chosen rp
    rp_deployable = # get deployable for RP
    if extra_specs refers to ``CUSTOM_FPGA_<vendor>_REGION_<uuid>`` and
       extra_specs refers to ``bitstream:<uuid>``:
       bitstream = glance.images.data(image_uuid)
       driver.program(bitstream, rp_deployable,  …)
    if extra_specs refers to ``CUSTOM_FPGA_<vendor>_FUNCTION_<uuid>`` and
       extra_specs refers to function UUID/name:
       region_type_uuid = # fetch from selected RP
       bitstreams = glance.images.list(...)
       # queries Glance by function UUID/name property and region type
       # UUID to get matching bitstreams
       if len(bitstreams) > 1:
         error(...) # bitstream choice policy is outside Cyborg
       driver.program(bitstream, rp_deployable, …)
    pci_bdf = driver.allocate_handle(...)
    # update Cyborg DB with instance_info and BDF usage
    return { “pci_id”: pci bdf }

  def unplug(instance_info):
    bdf_list = # fetch BDF usage from Cyborg DB for instance
    # update Cyborg DB to mark those BDFs as free
    return len(bdf_list)

Alternatives
------------

N/A

Data model impact
-----------------

None


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

* Decide how to associate multiple functions/bitstreams in extra specs
  with multiple devices in the flavor.

* Decide specific changes needed in Cyborg conductor, db, agent and drivers.

* Others: TBD

Dependencies
============

* Nested Resource Provider support in Nova

* `Nova Granular Requests
  <https://specs.openstack.org/openstack/nova-specs/specs/queens/approved/granular-resource-requests.html>`_

Testing
=======

For each vendor driver supported in this release, we need to integrate the
corresponding FPGA type(s) in the CI infrastructure.

Documentation Impact
====================

The behavior with respect to accelerators during various instance operations
(reboot, pause, etc.) must be documented. The procedure to upload a bitstream,
including applying Glance properties, must also be documented.

References
==========

.. [#CyborgNovaSched] `Cyborg Nova Scheduling Specification
  <https://review.openstack.org/#/c/554717/>`_

.. [#Bitstreamspec] `Cyborg bitstream metadata standardization spec
   <https://review.openstack.org/#/c/558265/>`_

.. [#ServerConcepts] `OpenStack Server API Concepts
   <https://developer.openstack.org/api-guide/compute/server_concepts.html>`_

History
=======

Optional section intended to be used each time the spec is updated to describe
new design, API or any database schema updated. Useful to let reader understand
what's happened along the time.

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Rocky
     - Introduced

