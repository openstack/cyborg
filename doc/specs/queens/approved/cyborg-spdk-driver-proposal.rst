..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===========================
Cyborg SPDK Driver Proposal
===========================

https://blueprints.launchpad.net/openstack-cyborg/+spec/cyborg-spdk-driver

This spec proposes to provide the initial design for Cyborg's SPDK driver.

Problem description
===================

SPDK is a high performance kit and provides a user space, polled-mode,
asynchronous, lockless NVMe driver for storage acceleration on the
backend. Our goal is to add a SPDK driver for Cyborg to manage SPDK,
and further improve storage performance.

Use Cases
---------

* When Cinder uses Ceph as its backend, the user should be able to
  use the Cyborg SPDK driver to discover the SPDK accelerator backend,
  enumerate the list of the Ceph nodes that have installed the SPDK.
* When Cinder directly uses SPDK's BlobStore as its backend, the user
  should be able to accomplish the same life cycle management operations
  for SPDK as mentioned above. After enumerating the SPDK, the user can
  attach (install) SPDK on that node. When the task completes, the user
  can also detach the SPDK from the node. Last but not least the user
  should be able to update the latest and available SPDK.

Proposed change
===============

In general, the goal is to develop the Cyborg SPDK driver that supports
discover/list/update/attach/detach operations for SPDK framework.

SPDK framework
--------------

The SPDK framework comprises of the following components::

        +-----------userspace--------+  +--------------+
        | +------+ +------+ +------+ | | +-----------+ |
  +---+ | |DPDK  | |NVMe  | |NVMe  | | | |   Ceph    | |
  | N +-+-+NIC   | |Target| |Driver+-+-+ |NVMe Device| |
  | I | | |Driver| |      | |      | | | +-----------+ |
  | C | | +------+ +------+ +------+ | | +-----------+ |
  +---+ | +------------------------+ | | | Blobstore | |
        | |     DPDK Libraries     | | | |NVMe Device| |
        | +------------------------+ | | +-----------+ |
        +----------------------------+ +---------------+

BlobStore NVMe Device Format
----------------------------

BlobStore owns the entire NVMe device including metadata management
and data management, which defines three basic units of disk space (like
logical block, page, cluster). The NVMe device is divided into clusters
starting from the first logical block.

LBA 0                                   LBA N
+-----------+-----------+-----+-----------+
| Cluster 0 | Cluster 1 | ... | Cluster N |
+-----------+-----------+-----+-----------+

Cluster0 has special format which consists of pages. Page0 is the
first page of Cluster0. Super Block contains the basic information of
BlobStore.

+--------+-------------------+
| Page 0 | Page 1 ... Page N |
+--------+-------------------+
| Super  |  Metadata Region  |
| Block  |                   |
+--------+-------------------+

Each blob is allocated a non-contiguous set of pages. These pages form
a linked list.
In general, the BlobStore adopts direct operation of bare metal device and
avoids the filesystem, which improves efficiency.

Life Cycle Management Phases
----------------------------
* We should be able to add a judgement whether the backend node has SPDK kit
  in generic driver module. If true, initialize the DPDK environment (such as
  hugepage).
* Import the generic driver module, and then we should be able to
  discover (probe) the system for SPDK.
* Determined by the backend storage scenario, enumerate (list) the optimal
  SPDK node, returning a boolean value to judge whether the SPDK should be
  attached.
* After the node where SPDK will be running is attached, we can now send a
  request about the information of namespaces, and then create an I/O queue
  pair to submit read/write requests to a namespace.
* When Ceph is used as the backend, as the latest Ceph (such as Luminous)
  uses the BlueStore to be the storage engine, BlueStore and BlobStore are
  very similar things. We will not be able to use BlobStore to accelerate
  Ceph, but we can use Ioat and poller to boost speed for storage.
* When SPDK is used as the backend, we should be able to use BlobStore to
  improve performance.
* Whenever user requests, we should be able to detach the SPDK device.
* Whenever user requests, we should be able to update SPDK to the latest and
  stable release.

Alternatives
------------

None

Data model impact
-----------------

* The Cyborg SPDK driver will notify Cyborg Agent to update the database
  when discover/list/update/attach/detach operations take place.

REST API impact
---------------

This blueprint proposes to add the following APIs:

* cyborg discover-driver（driver_type）
* cyborg driver-list(driver_type)
* cyborg install-driver(driver_id, driver_type)
* cyborg attach-instance <instance_id>
* cyborg detach-instance <instance_id>
* cyborg uninstall-driver(driver_id, driver_type)
* cyborg update-driver <driver_id, driver_type>

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

The SPDK can provide a user space, polled-mode, asynchronous,
lockless NVMe driver for storage acceleration on the backend.

Other deployer impact
---------------------

Deployers can call SPDK from the nodes which have installed SPDK
after the driver has been implemented.

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  luwei he <heluwei@huawei.com>

Work Items
----------

* Implement the cyborg-spdk-driver in this spec.
* Propose SPDK to py-spdk. The py-spdk is designed as a SPDK client
  which provides the python binding.


Dependencies
============

* Cyborg API Spec
* Cyborg Agent Spec
* Cyborg Driver Spec
* Cyborg Conductor Spec

Testing
========

* Unit tests will be added to test Cyborg SPDK driver.
* Functional tests will be added to test Cyborg SPDK driver. For example:
  discover-->list-->attach，whether the workflow can be passed successfully.

Documentation Impact
====================

Document SPDK driver in the Cyborg project

References
==========

* Cyborg API Spec
* Cyborg Agent Spec
* Cyborg Driver Spec
* Cyborg Conductor Spec


History
=======

.. list-table:: Revisions
   :header-rows: 1

   * - Release
     - Description
   * - Queens
     - Introduced
