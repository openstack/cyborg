============================
Intel NIC driver with SR-IOV
============================

Overview
========

This guide covers setting up the Cyborg Intel NIC driver with SR-IOV
for smartNIC VF passthrough to guests. The Intel NIC driver discovers
Intel NICs and their SR-IOV virtual functions (VFs), registers them as
accelerator resources in Placement, and works with Nova and Neutron to
attach VFs to instances via VFIO.

The smartNIC SR-IOV flow uses Cyborg to manage VF lifecycle (discovery,
scheduling via Placement, ARQ binding) while Neutron's SR-IOV agent
handles port binding on the assigned VF.

Prerequisites
=============

* A baremetal host with an Intel NIC that supports SR-IOV (e.g., X710,
  XXV710)
* IOMMU enabled on the host
* Basic understanding of SR-IOV and PCI passthrough

Enable IOMMU
============

Add ``intel_iommu=on iommu=pt`` to the kernel command line. For example,
on systems using GRUB:

.. code-block:: console

   $ sudo grubby --update-kernel=ALL --args="intel_iommu=on iommu=pt"
   $ sudo reboot

After reboot, verify IOMMU is active:

.. code-block:: console

   $ sudo dmesg | grep -i iommu | head -5
   [    0.649171] iommu: Default domain type: Passthrough (set via kernel command line)

Create VFs
==========

Create virtual functions on the NIC interface you want to use for
SR-IOV. This should be a non-management interface (do not use the
interface that carries SSH or API traffic).

.. code-block:: console

   $ echo 4 > /sys/class/net/ens1f1np1/device/sriov_numvfs

Replace ``ens1f1np1`` with your interface name and ``4`` with the
desired number of VFs. Verify they were created:

.. code-block:: console

   $ lspci | grep -i "virtual function"
   3b:0a.0 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
   3b:0a.1 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
   3b:0a.2 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
   3b:0a.3 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)

.. note::

   VFs persist until reboot or until a different number is written to
   ``sriov_numvfs``. To make them persistent across reboots, add a udev
   rule or systemd unit.

Deploy devstack
===============

A sample ``local.conf`` is provided at
``devstack/local-conf.intel-nic.sample`` in the Cyborg repository.
Copy it to your devstack checkout and adjust for your environment:

.. code-block:: console

   $ cp /opt/stack/cyborg/devstack/local-conf.intel-nic.sample \
        ~/devstack/local.conf

Key settings to adjust:

* ``HOST_IP``: your host's management IP address
* ``PHYSICAL_DEVICE_MAPPINGS``: ``public:<interface>`` for your
  SR-IOV interface (uses the same physnet as devstack's default
  flat network)
* ``physical_device_mappings`` in ``[x710_static]``: must match the
  above

Then run devstack:

.. code-block:: console

   $ cd ~/devstack
   $ ./stack.sh

Verify device discovery
=======================

After devstack completes, verify that Cyborg discovered the NIC and
its VFs:

.. code-block:: console

   $ source ~/devstack/openrc admin admin
   $ openstack accelerator device list
   $ openstack accelerator deployable list

You should see devices for each PF matching ``KNOWN_NICS`` and
deployables for each VF.

Create a device profile and port
================================

Create a device profile requesting a VF on your physical network:

.. code-block:: console

   $ openstack accelerator device profile create smartnic-vf \
       '[{"resources:CUSTOM_NIC": "1", "trait:CUSTOM_VF": "required", "trait:CUSTOM_PUBLIC": "required"}]'

The sample ``local.conf`` maps the SR-IOV interface to the ``public``
physnet, which is the same physnet devstack uses for its default flat
network. This means you can create SR-IOV ports directly on the
existing ``public`` network without creating a separate provider
network.

Create a port with the ``accelerator-direct`` vnic type and the device
profile:

.. code-block:: console

   $ openstack port create sriov-port \
       --network public \
       --vnic-type accelerator-direct \
       --device-profile smartnic-vf

Boot a VM
=========

Boot an instance using the SR-IOV port:

.. code-block:: console

   $ openstack server create test-sriov \
       --image <image> --flavor <flavor> \
       --port sriov-port --wait

.. note::

   Use an image with the ``iavf`` driver (e.g., Ubuntu, CentOS, RHEL).
   Minimal images like cirros lack the driver and will not be able to
   use the VF inside the guest.

Verify the VF was assigned:

.. code-block:: console

   $ openstack accelerator arq list
   $ openstack port show sriov-port

The ARQ should be in ``Bound`` state and the port should show
``binding_vif_type: hw_veb`` with ``binding_vnic_type:
accelerator-direct``.

Known limitations
=================

* The Intel NIC driver discovers all matching PCI devices, including
  management interfaces. There is no mechanism to exclude specific
  devices. Take care to avoid assigning management PFs/VFs to guests.

* ``KNOWN_NICS`` in ``cyborg/accelerator/drivers/nic/intel/sysinfo.py``
  is a hardcoded list of supported PCI device IDs. New NIC variants
  require a code change.

* The ``--vnic-type accelerator-direct`` CLI option requires
  python-openstackclient with the ``accelerator-direct`` choice added
  (see `LP#2161369 <https://bugs.launchpad.net/python-openstackclient/+bug/2161369>`_).

References
==========

* `Nova smartNIC SR-IOV spec <https://specs.openstack.org/openstack/nova-specs/specs/xena/implemented/sriov-smartnic-support.html>`_
* `Gerrit topic for smartNIC support <https://review.opendev.org/q/topic:%22bp/sriov-smartnic-support%22>`_
* :doc:`/contributor/devstack_setup` - General devstack setup guide
* :doc:`/contributor/driver-development-guide` - Driver development guide
