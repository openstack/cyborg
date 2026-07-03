=====
Build
=====

Local build
===========

Install headers for the running kernel, then build the module from the
repository root.

On Debian/Ubuntu:

.. code-block:: console

   $ sudo apt install linux-headers-$(uname -r) build-essential
   $ bash tools/check-kernel-config.sh
   $ make -C pci-sim modules

On CentOS/Fedora/RHEL:

.. code-block:: console

   $ sudo dnf install kernel-devel-$(uname -r) gcc make
   $ bash tools/check-kernel-config.sh
   $ make -C pci-sim modules

The module is created at ``pci-sim/fake_pci_sriov.ko``.

The build does not require a Linux git checkout.  It uses the kernel build
tree provided by the running kernel's header package:

.. code-block:: console

   $ make -C /lib/modules/$(uname -r)/build M=$PWD/pci-sim modules
