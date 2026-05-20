========
Overview
========

``fake_pci_sriov.ko`` is a self-contained test module for SR-IOV
control-plane flows without physical SR-IOV hardware.  It creates one or more
fake PCI host bridges, each with one physical function and software-created
virtual functions.  The VFs can be bound to VFIO and assigned to a QEMU guest,
which makes the module useful for OpenStack Nova, libvirt and QEMU testing.

The emulated VF payload is intentionally small: a 16550-style UART loopback.
That is enough to prove that a VF assigned through VFIO is visible and usable
inside an unmodified guest such as CirrOS.

The source currently lives under the top-level ``pci-sim/`` directory and is
built as an out-of-tree kernel module against
``/lib/modules/$(uname -r)/build``.
