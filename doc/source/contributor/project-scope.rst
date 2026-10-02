.. Licensed under the Apache License, Version 2.0 (the "License"); you may
   not use this file except in compliance with the License. You may obtain
   a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
   License for the specific language governing permissions and limitations
   under the License.

.. _project-scope:

Scope of the Cyborg project
===========================

Purpose
-------

This document records the intended scope of Cyborg. It guides feature
planning and review, but does not promise that Cyborg supports every example
listed here. The :doc:`/admin/support-matrix` records current driver and
operation support.

This is a living document about where Cyborg should evolve and which
responsibilities belong elsewhere. The examples help guide those decisions.
They are not a complete feature list or an implementation reference.

Mission
-------

Cyborg provides a vendor-neutral API for managing the lifecycle of local
devices and software-defined resources that cloud services allocate to
workloads. It hides device-specific operations behind common discovery,
allocation, preparation, and release semantics.

The term accelerator is broad in this context. It includes a local device, a
share of one, or a software-defined resource backed by delegated local
capacity that needs special lifecycle management before a workload can use it.
Examples include GPUs, FPGAs, cryptographic devices, smart NICs, and NVMe
devices. An operator explicitly delegates resources to Cyborg. Delegation is
operator authorization to manage a resource and may use configuration,
allow-lists, or explicit assignment. The mechanism may differ by driver, but
discovery alone is not delegation. Cyborg does not claim every resource on a
host.

The official Cyborg mission is published in the `OpenStack Technical
Committee governance documents
<https://governance.openstack.org/tc/reference/projects/cyborg.html#mission>`_.

Vendor-neutral API
------------------

Workload-facing requests describe the capabilities and results a workload
needs, rather than vendor commands or vendor-specific data models. This keeps
the public API vendor-neutral as it evolves.

Operator-facing discovery may expose vendor and product identity for device
selection, inventory, and diagnosis. Workloads request resources through
vendor-neutral device profiles and capabilities rather than vendor identity.

Cyborg prefers generic drivers that use standard operating system or device
interfaces. A vendor-specific driver is appropriate when those interfaces
cannot provide a required discovery or lifecycle operation.

Driver parity and interoperability
----------------------------------

A common lifecycle baseline lets clients use different device types through
the same API. That baseline covers discovery of delegated devices, capability
and inventory reporting, and allocation and release for each device type.
Drivers may also offer capabilities such as programming, partitioning, reset,
or cleaning.

A driver should declare its optional capabilities in code and document them.
Cyborg should be able to identify supported operations without attempting them.

Driver parity means that a capability has the same meaning across drivers,
without a vendor-specific interpretation of a generic request. Clients need a
way to discover supported capabilities and rely on consistent lifecycle
results. Parity does not mean identical hardware availability or performance.

Responsibilities
----------------

Service dependencies and integrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cyborg should support standalone use without a workload service.
Placement is a required dependency for supported deployments. Workload services
are optional integrations. A consuming workload integration coordinates
resource use for workloads managed by another service. A standalone client
coordinates resource use without a workload service.

Keystone is technically optional, but it is the only supported authentication
integration.

Device discovery and inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cyborg discovers resources that the operator has delegated to it. It records
their capabilities, attachment data, lifecycle state, and available partitions
or shares. It creates and updates only the device resource providers,
inventories, and traits that it is responsible for managing. Placement accounts
for those resources.

The consuming workload integration or standalone client creates and cleans up
Placement allocation claims. It also selects the host and resource provider,
usually through a workload scheduler. Cyborg realizes the selected resource
and may choose or create a concrete partition or slice within the selected
provider.

Device profiles and related metadata describe resource requirements and device
capabilities. They do not control compute, storage, network, or other behavior
owned by another service.

Allocation lifecycle
~~~~~~~~~~~~~~~~~~~~

A workload service or standalone client coordinates a resource request.
Cyborg translates the request into resource requirements, records the
allocation lifecycle, and binds the selected resource to that request. Cyborg
returns the information that the consuming service, client, or runtime needs
to attach the resource.

Cyborg does not choose the workload's host or Placement resource provider and
does not perform the final attachment to a virtual machine, container,
bare-metal workload, or other consumer. This keeps resource lifecycle
management separate from workload scheduling and runtime control.

Cyborg owns release and reclamation of its managed resources. The consuming
workload integration or standalone client owns workload teardown, final
detachment, and cleanup of Placement allocation claims.

Device preparation and reclamation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cyborg may change a delegated device when the change is part of an allocation
lifecycle. In-scope operations include:

* loading a workload-specific function, such as an FPGA bitstream;
* creating or removing a device partition or share;
* resetting a device before reuse; and
* cleaning or sanitizing a device before or after an allocation.

Cyborg currently supports static partitioning. Dynamic partitioning is within
the project's intended scope. Examples include mediated devices, virtual GPUs,
SR-IOV virtual functions, GPU partitions, and time-sliced resources.

These actions prepare a resource for a workload or return it to the allocatable
pool. They do not make Cyborg a general host, storage, or network management
service.

Software-defined resources
~~~~~~~~~~~~~~~~~~~~~~~~~~

An allocatable resource does not need to correspond one-to-one with a physical
device. Cyborg may manage a software-defined resource when it is backed by
capacity local to the host of the managing Cyborg agent. A workload may consume
the resulting resource remotely. The operator must delegate the backing
capacity to Cyborg, and the resource follows the same discovery, allocation,
preparation, and reclamation lifecycle as a hardware device.

For example, LVM could partition delegated local block capacity and create an
allocation-bound logical volume for a workload. The logical block device is the
allocated resource, while LVM is only the partitioning mechanism. This does not
make LVM itself an accelerator, create persistent volume semantics, or put
general LVM administration within Cyborg's scope.

Resources exposed through SPDK are another example. Cyborg may perform the
per-allocation configuration needed to create or remove a vhost or NVMe-oF
resource from delegated local capacity. Deployment tooling owns SPDK
installation and global configuration. The SPDK service owns ongoing data-plane
operation. These examples explain the intended resource model and do not
promise current support.

Scalability
-----------

Cyborg's design needs to accommodate deployments on a single node as well as
those with thousands of agents. API and conductor capacity should scale
independently, while agent work stays local to the hosts and devices that need
it. The allocation path needs to avoid fleet-wide synchronization and scans
of every managed resource. This constraint does not rule out normal Placement,
database, or service consistency operations.

Upgrades and compatibility
--------------------------

Cyborg's intended upgrade model follows the OpenStack release and SLURP
policies. Each release should support an upgrade from the previous release. A
SLURP release should also support an upgrade from the previous SLURP release.
The target rolling-upgrade model is designed to allow services from the target
release to coexist with Cyborg services up to two releases older.

Cyborg does not yet provide the object and RPC version negotiation needed for
this full rolling-upgrade model. Closing that gap is part of the project's
direction. Until then, the upgrade guide and release notes must state the
supported procedure and any required downtime.

Stable REST API behavior must remain compatible within its published
microversion contract. Cyborg does not provide an API extension framework; new
API functionality uses microversions. Behavior within a supported microversion
must remain compatible.

Cyborg may raise the minimum supported microversion, introduce a new major API
version, or retire a supported public capability. The project must announce
the deprecation no later than a SLURP release and continue support through at
least the following SLURP release. Deprecations must include release notes and
migration guidance. This SLURP-aligned policy applies to supported public APIs
and capabilities, not internal interfaces or unsupported external drivers.

Supported public lifecycle behavior should not change without a documented
migration path. Experimental capabilities must be identified through API
discovery, documentation, or release notes.

The Python driver interface is internal even though drivers are loaded through
stevedore. It has no stability guarantee. Out-of-tree drivers are possible,
but Cyborg does not support them. Their maintainers are responsible for
adapting them to each Cyborg release.

Third-party APIs and integrations
---------------------------------

Cyborg does not proxy, emulate, or add compatibility endpoints for vendor or
third-party APIs. External software may translate those APIs to the standard
Cyborg API without changing Cyborg's public contract.

Integrations that use another project or tool's supported public extension
points are in scope. Examples include workload-scheduler filters or weighers,
Tempest plugins, and OpenStackClient plugins. Scheduler extensions may expose
Cyborg resource requirements or capabilities to a workload scheduler. They do
not transfer ownership of scheduling policy or host and resource-provider
selection to Cyborg.

Cyborg should propose native integration to the owning project when
appropriate. If that project accepts the proposal, Cyborg may move the
integration there. Otherwise, Cyborg may maintain the plugin in its own source
tree or another Cyborg-owned repository.

A Cyborg-managed SmartNIC may be consumed through a Neutron port. Cyborg owns
the device lifecycle and reports its capabilities. Neutron owns network and
port behavior, while the consuming service or runtime performs final
attachment.

Deployment and packaging
------------------------

Cyborg maintains its standard Python source distribution and wheel for
publication to PyPI. It also maintains DevStack integration, test jobs, source
installation guidance, and configuration references.

Apart from its standard Python source distribution and wheel, Cyborg does not
maintain distribution packages, container images, production release
artifacts, or production deployment automation. DevStack is a development and
testing installer, not a production packaging system.

Cyborg may maintain long-term test artifacts that integrate with external
systems. For example, the ``pci-sim`` kernel module is maintained test
infrastructure, not a Cyborg deliverable. As an explicit test-only exception,
Cyborg test tooling may build, load, and unload it. This does not put
production kernel-module installation or management within the project's
scope. If an upstream project wants to adopt an artifact, Cyborg may work with
that project to move it upstream.

Security and discoverability
----------------------------

New capabilities must preserve least privilege, hard multi-tenancy, and safe
default behavior. Operators must explicitly delegate resources to Cyborg, and
access to lifecycle operations must follow the ownership and service boundaries
in this document.

Before Cyborg allocates a stateful resource to a different tenant, it must
remove data and device state left by the previous tenant. Cleaning may occur
after release or before the next allocation, but it must succeed before Cyborg
returns the resource to the allocatable pool. A cleanup failure keeps the
resource unavailable. This safety rule does not require a cleaning API for a
resource that cannot retain tenant data or state.

Clients must be able to discover supported API versions and device
capabilities. They must not have to infer support from a vendor name, driver
name, or deployment-specific assumption.

Scope boundaries
----------------

Cyborg does not manage:

* operating system or distribution packages, container images, production
  release artifacts other than its Python source distribution and wheel, or
  production deployment automation;
* installation, upgrade, replacement, or general configuration of kernel and
  device drivers;
* creation, packaging, installation, or maintenance of SELinux policy modules
  or AppArmor profiles;
* device firmware installation or upgrades;
* continuous device monitoring, telemetry, metrics collection, or alerting;
* device metrics or telemetry through the Cyborg REST API;
* hardware installation, host bootstrap, BIOS settings, or other machine
  provisioning;
* ownership of workload placement or scheduling policy, although Cyborg may
  provide integrations through supported scheduler extension points;
* workload creation, deletion, or runtime control;
* final attachment of a device to a workload;
* general block storage services, including persistent volume semantics,
  replication, backup, and data placement;
* general network services, including network creation, addressing, routing,
  and policy; or
* configuration and orchestration inside a workload.

Cyborg may call installed tools or drivers to perform an in-scope lifecycle
operation. For example, discovery may use ``lspci`` to identify PCI devices.
That does not make installation or maintenance of those tools part of Cyborg.
Cyborg may also read the device status needed to determine whether a resource
is allocatable or a lifecycle operation succeeded.

The main Cyborg REST API will never expose device metrics or telemetry. A
service-local endpoint may expose limited health information or metrics about
a Cyborg service. It must not expose device metrics or become a device
monitoring interface.

The same boundary applies to hardware and software-defined resources. Cyborg
may discover, prepare, allocate, reclaim, and perform per-allocation
configuration of resources created from delegated local capacity. It does not
provide general storage services or install, globally configure, or operate the
underlying software framework. Cyborg leaves the service delivered through an
allocated resource to the appropriate system.

Evaluating new work
-------------------

A proposed device-management feature fits Cyborg when it:

* acts on a local device or software-defined resource backed by capacity that
  an operator has delegated to Cyborg;
* supports discovery, allocation, preparation, use, release, or reclamation
  of that resource;
* exposes vendor-neutral capabilities and consistent lifecycle results;
* makes optional capabilities and API support discoverable;
* preserves hard multi-tenancy, safe defaults, compatibility, and the
  documented upgrade model;
* leaves host and resource-provider selection to the consuming integration or
  standalone client, with Placement accounting for the allocation; and
* does not replace a general compute, storage, network, deployment, firmware,
  monitoring, or machine provisioning service.

Client integrations, packaging, documentation, and test artifacts have their
own scope described above and need not act on a device directly.

When a proposal crosses one of these boundaries, Cyborg should provide the
smallest integration needed and leave the other responsibility with the
service that owns it.
