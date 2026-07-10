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

Each PF exposes a ``vf_personality`` sysfs file that controls what type of
VF device the PF creates, enabling mixed configurations on the same host.
PFs start with personality ``unset``; the user must assign a personality
before the PF can create VFs.  Currently supported personalities are
``uart`` and ``mdev``; additional types (e.g. NVMe) may be added in
the future.

When a PF is configured with an ``mdev`` personality,
it registers as an mdev parent and exposes two mdev types
(``sim_accel_small`` and ``sim_accel_large``), which allows Cyborg's
``GenericMdevDriver`` to be tested without real mdev-capable hardware.

The source currently lives under the top-level ``pci-sim/`` directory and is
built as an out-of-tree kernel module against
``/lib/modules/$(uname -r)/build``.
