====================================
Creating Development VMs for Testing
====================================

Overview
========

This guide provides instructions for creating a development virtual machine
(VM) for Cyborg testing and development. This is useful when you don't have
access to physical hardware with accelerator devices, or when you want to
test in an isolated environment.

The VM created using these instructions provides a foundation suitable for
Cyborg development with emulated devices like Nvme and passthrough scenarios.

Prerequisites
=============

Before creating a development VM, ensure you have:

* A Linux host system with sufficient resources (16GB+ RAM, 100GB+ disk space)
* Nested virtualization and IOMMU support enabled
* Basic DevStack knowledge (see :doc:`/contributor/devstack_setup`)

When to Use This Guide
======================

Use this guide when you need to:

* Create a VM for Cyborg development without physical accelerator hardware
* Test Cyborg with emulated devices (NVMe, GPU, etc.)
* Set up an isolated development environment

**Note:** If you already have a physical or cloud-based server with Ubuntu
installed, you can skip this guide and proceed directly to
:doc:`/contributor/devstack_setup`.

Host System Requirements
========================

Nested Virtualization Support
-----------------------------

Your host system must support nested virtualization to run VMs inside the
development VM, and nested virtualization must also be enabled **inside the
development VM** for nova instances to use KVM acceleration under DevStack.

For full setup instructions, including how to make the configuration
persistent across reboots, refer to the
`official DevStack nested virtualization guide <https://docs.openstack.org/devstack/latest/guides/devstack-with-nested-kvm.html>`_.

Host IOMMU Configuration (Optional)
-----------------------------------

.. note::

   **You only need to configure host IOMMU if:**

   * You are installing DevStack directly on the host (not in a VM), OR
   * You are passing a physical host device to the DevStack VM (PCI passthrough)

   **You do NOT need host IOMMU** to use vIOMMU (virtual IOMMU) inside the guest
   VM. The VM configuration in this guide already includes vIOMMU support via
   the Q35 machine type.

If you need to pass physical devices from your host to the VM, enable IOMMU
on the host system:

Check if IOMMU is enabled in your kernel:

.. code-block:: console

   $ sudo dmesg | grep -e IOMMU -e DMAR

You should see messages indicating IOMMU/DMAR is enabled. If not, you may need
to enable it in your BIOS/UEFI settings and add kernel parameters.

To enable IOMMU on the **host**, edit your bootloader configuration:

.. code-block:: console

   $ sudo vim /etc/default/grub
   # For Intel processors: add intel_iommu=on iommu=pt
   # For AMD processors:   add amd_iommu=on iommu=pt

Update GRUB and reboot:

.. code-block:: console

   $ sudo update-grub
   $ sudo reboot

Install Required Packages on Host
---------------------------------

Install QEMU, libvirt, and related tools:

On Ubuntu/Debian:

.. code-block:: console

   $ sudo apt update
   $ sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients \
     bridge-utils virt-manager virt-viewer virtinst ovmf

On Fedora/RHEL:

.. code-block:: console

   $ sudo dnf install -y qemu-kvm libvirt virt-manager virt-viewer \
     virt-install edk2-ovmf

Add your user to the libvirt group:

.. code-block:: console

   $ sudo usermod -aG libvirt $USER
   $ newgrp libvirt

Verify the installation:

.. code-block:: console

   $ sudo virsh list --all
   $ sudo systemctl status libvirtd

Download Ubuntu Server Image
============================

Download the Ubuntu 24.04 LTS server ISO:

.. code-block:: console

   $ cd /var/lib/libvirt/images/
   $ sudo wget https://releases.ubuntu.com/24.04/ubuntu-24.04.4-live-server-amd64.iso

Create VM Using virsh
=====================

Create VM Disk Image
--------------------

Create a 50GB qcow2 disk image for the VM (25–50GB is sufficient for a
standard DevStack all-in-one setup; increase if you need extra space for
driver-specific devices such as NVMe emulation):

.. code-block:: console

   $ sudo qemu-img create -f qcow2 /var/lib/libvirt/images/devstack.qcow2 50G

Prepare VM Configuration
------------------------

The Cyborg repository includes a VM XML definition at
``devstack/cyborg_vm.xml``. Copy it and customize for your environment:

.. code-block:: console

   $ cd <cyborg-repo>
   $ cp devstack/cyborg_vm.xml /tmp/cyborg-devstack.xml

Edit ``/tmp/cyborg-devstack.xml`` to customize:

* **Memory**: Adjust the ``<memory>`` value based on your system
  (default: 12GB)
* **CPUs**: Adjust the ``<vcpu>`` count based on availability (default: 4)
* **Disk path**: Update the disk ``<source file>`` path to match your disk
  location
* **Disk size**: You can create a larger/smaller disk as needed

Define and Start VM
-------------------

Define the VM in libvirt:

.. code-block:: console

   $ sudo virsh define /tmp/cyborg-devstack.xml

Insert the Ubuntu installation ISO into the CDROM device:

.. code-block:: console

   $ sudo virsh change-media cyborg-devstack sda \
       /var/lib/libvirt/images/ubuntu-24.04.4-live-server-amd64.iso --insert

Start the VM and connect to the console:

.. code-block:: console

   $ sudo virsh start cyborg-devstack
   $ virt-viewer --connect qemu:///system --wait cyborg-devstack

The VM uses UEFI firmware (OVMF) via ``/usr/share/OVMF/OVMF_CODE.fd``,
which is provided by the ``ovmf`` (Ubuntu) or ``edk2-ovmf`` (Fedora)
package. When you start the VM with the ISO inserted, UEFI will boot the
Ubuntu installer from the CDROM. After installation, UEFI writes a boot
entry for the installed system to NVRAM and will boot from the hard disk
automatically on subsequent reboots.

Complete Ubuntu Installation
----------------------------

Follow the Ubuntu Server installation wizard in the console window (see the
Ubuntu Installation section below for detailed steps).

Ubuntu Installation
-------------------

Follow the Ubuntu Server installation wizard:

1. Select language: English
2. Base of installation: Ubuntu Server
3. Configure network (use DHCP or configure static IP)
4. Skip proxy address configuration
5. Wait for Ubuntu archive mirror configuration
6. Guided storage configuration: Use entire disk
7. Continue with storage configuration
8. Profile configuration:

   - Server name: ``cyborg-devstack``
   - Pick a username and password (using ``stack`` is recommended for
     consistency with DevStack conventions)
   - Enable "Install OpenSSH server"
   - Import SSH key (optional)

9. Wait for installation to complete and reboot.


When the installation completes, eject the ISO before rebooting:

.. code-block:: console

   $ sudo virsh change-media cyborg-devstack sda --eject
   $ sudo virsh reboot cyborg-devstack

UEFI will boot from the installed Ubuntu system on the hard disk.

Key VM Features
---------------

The VM defined in the XML configuration includes these key features:

* **Q35 machine type**: Required for IOMMU and PCIe device passthrough
* **host-passthrough CPU**: Provides nested virtualization support
* **12GB RAM, 4 vCPUs** (as defined in the XML): Minimum is 8GB RAM and
  4 vCPUs for an all-in-one DevStack node; 8 vCPUs is recommended
* **UEFI firmware (OVMF)**: Manages boot order via NVRAM; boots the installer
  ISO on first start, then automatically boots the installed system after
  the ISO is ejected

After installation, you can add driver-specific devices (such as NVMe
controllers, GPUs, etc.) as needed. Refer to the respective driver
documentation for device-specific setup.

.. note::

   The VM configuration used in this guide is based on the XML definition at
   ``<cyborg-repo>/devstack/cyborg_vm.xml``. This file can be customized further
   for driver-specific device additions.

Post-Installation Configuration
===============================

After the VM reboots, log in through the console or SSH.

Find VM IP Address
------------------

From the host system, find the VM's IP address:

.. code-block:: console

   $ sudo virsh domifaddr cyborg-devstack
   Name       MAC address          Protocol     Address
   -------------------------------------------------------------------------------
   vnet0      52:54:00:df:1c:96    ipv4         192.168.122.100/24

SSH Access
----------

SSH to the VM from your host:

.. code-block:: console

   $ ssh stack@192.168.122.100

Configure Passwordless sudo
---------------------------

For DevStack to work properly, configure passwordless sudo:

.. code-block:: console

   $ echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/$USER

System Update
-------------

Update the system packages:

.. code-block:: console

   $ sudo apt update
   $ sudo apt upgrade -y

Hostname Resolution
-------------------

Add the VM hostname to ``/etc/hosts`` for proper name resolution:

.. note:: Replace below ip with vm ip.

.. code-block:: console

   $ echo "<ip> $(hostname)" | sudo tee -a /etc/hosts

Verify that host ip address is displayed:

.. code-block:: console

   $ hostname -i
   <vm ip>

Next Steps
==========

Your base development VM is now ready. The typical workflow is:

1. **Install DevStack**: Follow :doc:`/contributor/devstack_setup` to install
   OpenStack with Cyborg enabled.

References
==========

* :doc:`/contributor/devstack_setup` - DevStack setup guide for Cyborg
* `libvirt Domain XML format <https://libvirt.org/formatdomain.html>`_
* `QEMU Machine Types <https://www.qemu.org/docs/master/system/qemu-manpage.html#hxtool-5>`_
* `DevStack with nested KVM <https://docs.openstack.org/devstack/latest/guides/devstack-with-nested-kvm.html>`_
