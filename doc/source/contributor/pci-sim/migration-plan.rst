=====================
Future migration work
=====================

The fake VF device state is small: UART registers plus FIFO contents.  A future
migration implementation should preserve enough state that a guest's
assigned VF continues to function after live migration.

Initial phases
==============

#. Add UART state save/restore helpers independent of VFIO migration plumbing.
#. Wire the current VFIO PCI migration APIs into ``pci_sim_vfio_pci``.
#. Validate with matching fake PF/VF topology on source and destination hosts.
#. Add Nova/libvirt level tests once QEMU behavior is understood.

This is intentionally future work.  The first goal for this repository is a
reliable out-of-tree build and local load/test flow for the current
Ubuntu 26.04 kernel.
