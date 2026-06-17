=======
Testing
=======

The local test environment assumes passwordless ``sudo``, matching typical
DevStack usage.

Host loopback smoke test
========================

.. code-block:: console

   $ make -C pci-sim modules
   $ sudo modprobe vfio-pci
   $ sudo insmod pci-sim/fake_pci_sriov.ko
   $ sudo pci-sim/test_pci_sim_loopback.py
   $ sudo pci-sim/cleanup_fake_pci_sriov.sh

QEMU/VFIO smoke test
====================

.. code-block:: console

   $ make -C pci-sim modules
   $ MODULE=./pci-sim/fake_pci_sriov.ko pci-sim/run_fake_pci_qemu_vfio_smoke.sh

The QEMU helpers bind a fake VF to ``pci_sim_vfio_pci`` and verify that QEMU
can start with the assigned VF.  CirrOS-based helpers are also included for
guest-level UART loopback testing.

DevStack Nova/Cyborg serial echo test
======================================

After stacking with the pci-sim DevStack plugin and its generated test
flavors, run the end-to-end helper from the repository root:

.. code-block:: console

   $ tools/run-devstack-serial-echo-test.sh

The helper uses ``openstack --os-cloud devstack-admin`` by default.  It
creates one VM at a time on the ``private`` network using the
``pci-sim-nova`` and ``pci-sim-cyborg`` flavors, opens the current
project's default security group for ICMP and SSH, attaches a temporary
floating IP, SSHes into CirrOS with the default ``cirros``/``gocubsgo``
credentials, verifies the passed-through serial PCI device, checks the UART
echo path, and then deletes the test VM and tagged floating IP.  Use
``--cleanup`` to remove leftovers from interrupted runs.
