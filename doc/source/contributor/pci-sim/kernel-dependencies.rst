===================
Kernel dependencies
===================

The original in-tree Kconfig dependency was::

   PCI && PCI_DOMAINS && IOMMU_API && VFIO_PCI_CORE && TTY

As an out-of-tree module, these are checked against
``/boot/config-$(uname -r)`` by ``tools/check-kernel-config.sh``.

Required options
================

The following options must be enabled in the running kernel configuration:

* ``CONFIG_MODULES=y``
* ``CONFIG_PCI=y``
* ``CONFIG_PCI_DOMAINS=y``
* ``CONFIG_IOMMU_API=y``
* ``CONFIG_TTY=y``
* ``CONFIG_VFIO=y`` or ``m``
* ``CONFIG_VFIO_PCI_CORE=y`` or ``m``

Runtime/test options
====================

The smoke tests are more useful when these are also enabled:

* ``CONFIG_PCI_IOV``
* ``CONFIG_VFIO_PCI``
* ``CONFIG_KVM``

The initial compatibility target is the current Ubuntu 26.04 generic kernel,
``7.0.0-15-generic``.  Broader Ubuntu 26.04 kernel update compatibility should
be added by version-guarding specific API differences as they are found.
