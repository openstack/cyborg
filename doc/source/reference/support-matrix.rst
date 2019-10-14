=====================
Cyborg Support Matrix
=====================

Cyborg supports specific operations on VMs with attached accelerator
resources, which are generally a subset of the full set of VM operations
supported by Nova (`nova-vm-ops
<https://docs.openstack.org/api-guide/compute/server_concepts.html>`_).

In this release, these operations have a dependency on specific Nova
patches (`nova-patches
<https://review.opendev.org/#/q/status:open+project:openstack/nova+bp/nova-cyborg-interaction>`_).
They can be expected to work in Cyborg only
if and when these Nova patches get merged without significant changes.
These operations are not supported in this release since the dependencies
are not met.

.. list-table:: VM Operations Expected to Work With Nova Dependencies
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

Operations not listed here may or may not work.

Driver Support
~~~~~~~~~~~~~~

The list of drivers available as part of the Cyborg distribution
at the time of release can be found in:
``cyborg.accelerator.driver`` section of `Cyborg's setup.cfg
<https://opendev.org/openstack/cyborg/src/branch/master/setup.cfg>`_

The following table provides additional information for individual drivers.

.. include:: driver-table.rst
