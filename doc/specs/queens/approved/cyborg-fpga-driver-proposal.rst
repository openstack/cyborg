..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===========================
Cyborg FPGA Driver Proposal
===========================

https://blueprints.launchpad.net/openstack-cyborg/+spec/cyborg-fpga-driver

This spec proposes to provide the initial design for Cyborg's FPGA driver.

Problem description
===================

A Field Programmable Gate Array(FPGA) is an integrated circuit designed to be
configured by a customer or a designer after manufacturing. The advantage lies
in that they are sometimes significantly faster for some applications because
of their parallel nature and optimality in terms of the number of gates used
for a certain process. Hence, using FPGA for application acceleration in cloud
has been becoming desirable.

There is a management framwork in Cyborg [1]_ for heterogeneous accelerators,
tracking and deploying FPGAs. This spec will add a FPGA driver for Cyborg to
manage specific FPGA devices.

Use Cases
---------

* When Cyborg agent starts or does resource checking periodically, the Cyborg
  FPGA driver should enumerate the list of the FPGA devices, and report the
  details of all available FPGA accelerators on the host, such as BDF(Bus,
  Device, Function), PID(Product id) VID(Vendor id), IMAGE_ID and PF(Physical
  Function)/VF(Virtual Function) type.

* When user uses empty FPGA regions as their accelerators, Cyborg agent will
  call driver's program() interface. Cyborg agent should provide BDF
  of PF/VF, and local image path to the driver. More details can be found in
  ref [2]_.

* When there maybe more thant one vendor fpga card on a host, or on different
  hosts in the cluster, Cyborg agent can discover the wendors easiy and
  intelligently by Cyborg FPGA driver, and call the correct driver to execute
  it's operations, such as discover() and program().


Proposed changes
================

In general, the goal is to develop a Cyborg FPGA driver that supports
discover/program interfaces for FPGA accelerator framework.

The driver should include the follow functions:
1. discover()
driver reports devices as following::

  [{
    "vendor": "0x8086",
    "product": "bcc0",
    "pr_num": 1,
    "devices": "0000:be:00:0",
    "path": "/sys/class/fpga/intel-fpga-dev.0",
    "regions": [
      {"vendor": "0x8086",
        "product": "bcc1",
        "regions": 1,
        "devices": "0000:be:00:1",
        "path": "/sys/class/fpga/intel-fpga-dev.1"
      }]
  }]

  pr_num: partial reconfiguration region numbers.

2. program(device_path, image)
   program the image to a PR region specified by device_path.
   device_path: the sys path of accelerator device.
   image: The local path of programming image.

Image Format
----------------------------

Alternatives
------------

None

Data model impact
-----------------

FPGA driver will not touch Data model.
The Cyborg Agent can call FPGA driver to update the database
during the discover/program operations.

REST API impact
---------------

The related FPGA accelerator APIs is out of scope for this spec.
The FPGA management framework for Cyborg [1]_ will alter the proposal.

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

Deployers should install the specific FPGA management stack that the driver
depends on.

Please see ref [2]_ for details.

Developer impact
----------------

There will be some developer impact vis-à-vis new functionality that
will be available to devs.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Shaohe Feng <shaohe.feng@intel.com>
  Dolpher Du <dolpher.du@intel.com>

Work Items
----------

* Implement the cyborg-fpga-driver in this spec.

Dependencies
============

* Cyborg API Spec
* Cyborg Agent Spec
* Cyborg Driver Spec
* Cyborg Conductor Spec

Testing
========

* Unit tests will be added to test Cyborg FPGA driver.
* Functional tests will be added to test Cyborg FPGA driver.

Documentation Impact
====================

Document FPGA driver in the Cyborg project

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

References
==========
.. [1] https://blueprints.launchpad.net/openstack-cyborg/+spec/cyborg-fpga-modelling
.. [2] https://01.org/OPAE
