=====================
Cyborg Support Matrix
=====================

Cyborg supports specific operations on VMs with attached accelerator
resources, which are generally a subset of the full set of VM operations
supported by Nova [nova-vm-ops]_. These are the operations that have been
validated to work in this release.

This document lists the supported operations on VMs with accelerators in this
release, with caveats as needed, and also the list of VM operations known not
to work. Other VM operations outside both lists may or may not work; users try
them at their own risk.

For the Train release, to enable the following VM operations are supported,
you must install certain Nova patches on top of the standard release
[nova-patches]_.

.. list-table:: Supported VM Operations
   :header-rows: 1

   * - VM Operation
     - Command
   * - VM creation
     - ``openstack server create``
   * - VM deletion
     - ``openstack server delete``
   * - Reboot within VM
     - ``ssh to VM and reboot in OS``
   * - Soft reboot
     - ``openstack server reboot --soft``
   * - Pause/Unpause
     - ``openstack server pause``, ``openstack server unpause``
   * - Lock/Unlock
     - ``openstack server lock``, ``openstack server unlock``

.. list-table:: VM Operations Known to Fail
   :header-rows: 1

   * - VM Operation
     - Command
   * - Hard Reboot
     - ``openstack server reboot --hard``
   * - Stop/Start
     - ``openstack server stop``, ``openstack server start``
   * - Suspend/Resume
     - ``openstack server suspend``, ``openstack server resume``


The following support matrix reflects the drivers that are currently
available or are available in
`cyborg.accelerator.driver section of Cyborg's setup.cfg
<https://opendev.org/openstack/cyborg/src/branch/master/setup.cfg>`_
at the time of release.

FPGA Driver Support
~~~~~~~~~~~~~~~~~~~~

The following table of drivers lists support status for FPGA accelerators

.. support_matrix:: support-matrix-fpga.ini

GPU Driver Support
~~~~~~~~~~~~~~~~~~~

The following table of drivers lists support status for GPU accelerators

.. support_matrix:: support-matrix-gpu.ini

Driver Removal History
~~~~~~~~~~~~~~~~~~~~~~

The section will be used to track driver removal starting from the Train
release.

* Train

References
~~~~~~~~~~

.. [nova-vm-ops] `Server concepts
   <https://docs.openstack.org/api-guide/compute/server_concepts.html>`_

.. [nova-patches] `Nova patches needed for VMs with accelerators
   <https://review.opendev.org/#/q/status:open+project:openstack/nova+bp/nova-cyborg-interaction>`_
