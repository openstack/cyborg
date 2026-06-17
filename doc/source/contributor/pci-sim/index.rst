.. _pci-sim:

=======
pci-sim
=======

``pci-sim`` provides an out-of-tree build of the ``fake_pci_sriov`` Linux
kernel module for DevStack and CI testing of SR-IOV PCI passthrough flows
without physical SR-IOV hardware.  It is included in the Cyborg repository
under the top-level ``pci-sim/`` directory and is built and loaded
automatically by the Cyborg DevStack plugin.

.. toctree::
   :maxdepth: 2

   overview
   build
   devstack
   testing
   kernel-dependencies
   migration-plan
