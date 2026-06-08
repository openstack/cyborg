=============================================
Cyborg NVMe driver development environment
=============================================

Overview
========

This guide provides instructions for configuring NVMe (Non-Volatile Memory
Express) and virtio-rng (Random Number Generator) device emulation and setting
up the PCI driver in Cyborg for development and testing.

The PCI driver in Cyborg enables passthrough of PCI devices (including NVMe
controllers and RNG devices) to instances. This guide covers the complete setup
from adding emulated devices to a development VM through verifying device
discovery in Cyborg.

Prerequisites
=============

Before following this guide, ensure you have:

* A development VM created and configured (see :doc:`/contributor/vm-setup`)
* SSH access to your development VM
* Basic understanding of PCI passthrough and device management

.. important::

   Add NVMe devices and configure vIOMMU **before** installing DevStack. The
   devices need to be present when Cyborg agent starts for proper discovery.

Scope
=====

This guide covers:

* Verifying QEMU NVMe device support on the host
* Adding NVMe devices to an existing libvirt VM
* Adding virtio-rng devices to an existing libvirt VM (optional)
* Configuring the PCI driver in DevStack/Cyborg
* Verifying device discovery in Cyborg

Verify NVMe Support
===================

On your host system (not inside the VM), verify that QEMU supports NVMe device
emulation:

.. code-block:: console

   $ qemu-kvm -device help | grep nvme
   name "nvme", bus PCI
   name "nvme-ns", bus nvme-bus
   name "nvme-subsys"

If you see output similar to above, NVMe device emulation is supported.

Enable vIOMMU Support
=====================

Before adding NVMe devices, enable virtual IOMMU (vIOMMU) in the VM. This is
**required** for PCI device passthrough - without it, Cyborg can discover
devices but cannot bind them to instances.

.. important::

   Enable vIOMMU **before** installing DevStack. Cyborg and Nova rely on IOMMU
   groups for device management and instance attachment.

Shutdown the VM
---------------

Before modifying the VM configuration, shut it down gracefully:

.. code-block:: console

   $ sudo virsh shutdown cyborg-devstack

Wait for the VM to shut down completely:

.. code-block:: console

   $ sudo virsh list --all
   Id   Name              State
   ------------------------------------
   -    cyborg-devstack   shut off

Add vIOMMU Configuration
------------------------

Edit the VM XML configuration:

.. code-block:: console

   $ sudo virsh edit cyborg-devstack

Add the vIOMMU configuration inside the ``<devices>`` section, before the
closing ``</devices>`` tag:

.. code-block:: xml

   <iommu model='intel'>
     <driver intremap='on' caching_mode='on' eim='on' iotlb='on'/>
   </iommu>

Save and exit (in vim: ``:wq``).

Start the VM
------------

Start the VM with vIOMMU enabled:

.. code-block:: console

   $ sudo virsh start cyborg-devstack

Verify vIOMMU is Working
-------------------------

SSH into the VM and verify IOMMU groups exist:

.. code-block:: console

   $ ssh <username>@<vm-ip-address>
   $ find /sys/kernel/iommu_groups/ -type l | wc -l
   15

This should return a non-zero value (typically 10-20 depending on VM
configuration). If zero, vIOMMU is not working - check the XML configuration.

Add NVMe Devices to VM
======================

Now that vIOMMU is enabled, you can add NVMe devices to the VM using native
libvirt configuration.

The Cyborg repository includes a complete VM definition with vIOMMU and NVMe
devices at ``<cyborg-repo>/devstack/cyborg_vm.xml`` for reference.

Shutdown the VM
---------------

Before adding NVMe devices, shut down the VM again:

.. code-block:: console

   $ sudo virsh shutdown cyborg-devstack

Wait for the VM to shut down completely:

.. code-block:: console

   $ sudo virsh list --all
   Id   Name              State
   ------------------------------------
   -    cyborg-devstack   shut off

Create NVMe Backing Storage
----------------------------

Create a qcow2 disk image to back the emulated NVMe device:

.. code-block:: console

   $ sudo qemu-img create -f qcow2 /var/lib/libvirt/images/nvme-disk1.qcow2 10G

Set proper ownership:

.. code-block:: console

   $ sudo chown qemu:qemu /var/lib/libvirt/images/nvme-disk1.qcow2

Edit VM Configuration
---------------------

Edit the VM XML to add NVMe device configuration:

.. code-block:: console

   $ sudo virsh edit cyborg-devstack

Add an NVMe controller inside the ``<devices>`` section:

.. code-block:: xml

   <controller type='nvme' index='0'/>

Add the NVMe disk configuration inside the ``<devices>`` section, after other
disk definitions:

.. code-block:: xml

   <disk type='file' device='disk'>
     <driver name='qemu' type='qcow2'/>
     <source file='/var/lib/libvirt/images/nvme-disk1.qcow2'/>
     <target dev='nvme0n1' bus='nvme'/>
     <serial>NVME0001</serial>
   </disk>

**Explanation of NVMe configuration:**

* ``<controller type='nvme' index='0'/>``: Creates an NVMe controller for
  attaching NVMe namespaces

* ``<disk type='file' device='disk'>``: Defines an NVMe disk device

  * ``<driver name='qemu' type='qcow2'/>``: Uses QEMU with qcow2 format
  * ``<source file='/var/lib/libvirt/images/nvme-disk1.qcow2'/>``: Path to the
    backing storage
  * ``<target dev='nvme0n1' bus='nvme'/>``: Attach as NVMe device nvme0n1
  * ``<serial>NVME0001</serial>``: Serial number for the NVMe controller
    (required)

Save and exit the editor (in vim: ``:wq``).

**Reference:** For a complete VM XML example with NVMe devices, see
``<cyborg-repo>/devstack/cyborg_vm.xml``.

Add RNG Device (Optional)
--------------------------

You can also add a virtio-rng (Random Number Generator) device to the VM for
additional PCI device testing. This is useful for testing multiple device
types with the PCI driver.

Edit the VM XML configuration:

.. code-block:: console

   $ sudo virsh edit cyborg-devstack

Add the RNG device configuration inside the ``<devices>`` section:

.. code-block:: xml

   <rng model='virtio'>
     <rate bytes='1024' period='1000'/>
     <backend model='random'>/dev/urandom</backend>
     <address type='pci' domain='0x0000' bus='0x06' slot='0x00' function='0x0'/>
   </rng>

**Explanation of RNG configuration:**

* ``<rng model='virtio'>``: Creates a virtio-based RNG device
* ``<rate bytes='1024' period='1000'>``: Limits entropy generation to 1024
  bytes per second (optional but recommended)
* ``<backend model='random'>/dev/urandom</backend>``: Uses host's /dev/urandom
  as entropy source
* ``<address type='pci' ...>``: Assigns a specific PCI address to the device
  (adjust bus/slot numbers to avoid conflicts with existing devices)

**Note:** The RNG device is already included in the reference VM XML at
``<cyborg-repo>/devstack/cyborg_vm.xml``.

Save and exit the editor (in vim: ``:wq``).

Start the VM
------------

Start the VM with the new NVMe and RNG device configuration:

.. code-block:: console

   $ sudo virsh start cyborg-devstack

Verify NVMe Devices in VM
==========================

SSH to the VM and verify that the NVMe device is visible.

Install Required Tools
----------------------

Install PCI utilities and NVMe tools:

.. code-block:: console

   $ sudo apt update
   $ sudo apt install -y pciutils nvme-cli

List PCI Devices
----------------

List all PCI devices to find the NVMe controller:

.. code-block:: console

   $ lspci -nn | grep -i non-volatile
   00:12.0 Non-Volatile memory controller [0108]: Red Hat, Inc. QEMU NVMe Controller [1b36:0010] (rev 02)

Note the vendor ID (``1b36``) and product ID (``0010``) - you'll need these for
the PCI driver configuration.

List NVMe Devices
-----------------

Use nvme-cli to list NVMe devices:

.. code-block:: console

   $ sudo nvme list
   Node             SN                   Model                                    Namespace Usage                      Format           FW Rev
   ---------------- -------------------- ---------------------------------------- --------- -------------------------- ---------------- --------
   /dev/nvme0n1     NVME0001             QEMU NVMe Ctrl                           1          10.74  GB /  10.74  GB    512   B +  0 B   1.0

Verify the device appears as ``/dev/nvme0n1``:

.. code-block:: console

   $ ls -l /dev/nvme*
   crw------- 1 root root 243, 0 Jan 15 10:30 /dev/nvme0
   brw-rw---- 1 root disk 259, 0 Jan 15 10:30 /dev/nvme0n1

Verify RNG Device (if added)
-----------------------------

If you added the virtio-rng device, verify it appears in the PCI device list:

.. code-block:: console

   $ lspci -nn | grep -i virtio
   00:13.0 Unclassified device [00ff]: Red Hat, Inc. Virtio RNG [1af4:1044] (rev 01)

Note the vendor ID (``1af4``) and product ID (``1044``) - you'll need these if
you want to add the RNG device to the PCI driver whitelist.

Verify the RNG device is functional:

.. code-block:: console

   $ cat /sys/devices/virtual/misc/hw_random/rng_available
   virtio_rng.0

   $ cat /sys/devices/virtual/misc/hw_random/rng_current
   virtio_rng.0

Configure PCI Driver in DevStack
=================================

The PCI driver in Cyborg requires configuration to specify which PCI devices
should be managed. This is done by adding PCI passthrough whitelist entries
to the Cyborg configuration.

Update local.conf
-----------------

Edit your DevStack ``local.conf`` file to enable the PCI driver and configure
the passthrough whitelist.

In your ``~/devstack/local.conf`` file, add or update the following sections:

.. code-block:: ini

   # Enable both fake and PCI drivers
   # --------------------------------
   CYBORG_ENABLED_DRIVERS=fake_driver,pci_driver

   # Configure PCI passthrough whitelist for NVMe device
   # ---------------------------------------------------
   # Find device IDs with: lspci -nn | grep -i Non-Volatile
   # Example: Red Hat QEMU NVMe Controller [1b36:0010]

   [[post-config|$CYBORG_CONF]]
   [pci]
   # NVMe device passthrough (vendor_id: 1b36, product_id: 0010)
   passthrough_whitelist='{"vendor_id":"1b36","product_id":"0010"}'

   # To add multiple devices including virtio-rng, use a JSON array:
   # passthrough_whitelist='[{"vendor_id":"1b36","product_id":"0010"},{"vendor_id":"1af4","product_id":"1044"}]'

**Configuration explanation:**

* ``CYBORG_ENABLED_DRIVERS``: Enables both the fake driver (for testing) and
  the PCI driver
* ``[[post-config|$CYBORG_CONF]]``: Adds configuration to ``cyborg.conf``
  after DevStack generates it
* ``[pci]``: Configuration section for the PCI driver
* ``passthrough_whitelist``: JSON string specifying which PCI devices to manage

  * ``vendor_id``: PCI vendor ID (found using ``lspci -nn``)
  * ``product_id``: PCI product ID (found using ``lspci -nn``)

**Managing Multiple Device Types**

To manage multiple device types (e.g., NVMe + RNG), specify multiple whitelist
entries as a JSON array:

.. code-block:: ini

   [[post-config|$CYBORG_CONF]]
   [pci]
   # Whitelist both NVMe and virtio-rng devices
   passthrough_whitelist='[{"vendor_id":"1b36","product_id":"0010"},{"vendor_id":"1af4","product_id":"1044"}]'

This configuration enables:

* NVMe device: ``vendor_id=1b36, product_id=0010`` (QEMU NVMe Controller)
* RNG device: ``vendor_id=1af4, product_id=1044`` (Virtio RNG)

Finding Device IDs
~~~~~~~~~~~~~~~~~~

To find the vendor and product IDs for any PCI device:

.. code-block:: console

   $ lspci -nn
   ...
   00:12.0 Non-Volatile memory controller [0108]: Red Hat, Inc. QEMU NVMe Controller [1b36:0010] (rev 02)
   ...

The format is ``[vendor_id:product_id]``, so ``[1b36:0010]`` means:

* Vendor ID: ``1b36`` (Red Hat, Inc.)
* Product ID: ``0010`` (QEMU NVMe Controller)

Run DevStack
============

After updating ``local.conf``, run DevStack to apply the configuration:

.. code-block:: console

   $ cd ~/devstack
   $ ./stack.sh

This will take 30-60 minutes to complete. The PCI driver will be loaded and
will discover the whitelisted PCI devices.

For complete DevStack setup instructions, see
:doc:`/contributor/devstack_setup`.

Verify Device Discovery
========================

After DevStack completes successfully, verify that Cyborg has discovered the
NVMe and other PCI devices.

Source OpenStack Credentials
-----------------------------

.. code-block:: console

   $ source ~/devstack/openrc admin admin

List Accelerator Devices
-------------------------

.. code-block:: console


   $ openstack accelerator device list
   +--------------------------------------+------+--------+-----------------+------------------------------------------------+
   | uuid                                 | type | vendor | hostname        | std_board_info                                 |
   +--------------------------------------+------+--------+-----------------+------------------------------------------------+
   | ece74dd7-c15f-4dca-b68f-f6fe189fcc1e | GPU  | 1af4   | cyborg-devstack | {"product_id": "1044", "controller": null}     |
   | 57763ef1-47cf-46b2-9d1d-047a16daf90b | FPGA | 0xABCD | cyborg-devstack | {"device_id": "0xabcd", "class": "Fake class"} |
   | 815146e7-48a3-4906-a0b5-47aee53abada | GPU  | 1b36   | cyborg-devstack | {"product_id": "0010", "controller": null}     |
   +--------------------------------------+------+--------+-----------------+------------------------------------------------+

**Expected output:**

* **Fake FPGA device**: Provided by the ``fake_driver`` for testing

  * Type: ``FPGA``
  * Vendor: ``0xABCD``

* **NVMe device**: Managed by the ``pci_driver``

  * Type: ``GPU`` (the PCI driver uses GPU as a generic type for PCI devices)
  * Vendor: ``1b36`` (Red Hat, Inc.)
  * Product: ``0010`` (QEMU NVMe Controller)

* **RNG device** (if enabled in whitelist): Managed by the ``pci_driver``

  * Type: ``GPU`` (the PCI driver uses GPU as a generic type for PCI devices)
  * Vendor: ``1af4`` (Red Hat, Inc.)
  * Product: ``1044`` (Virtio RNG)

**Note:** The PCI driver reports all managed PCI devices with type ``GPU`` -
this is expected behavior and does not indicate an error. The actual device
type can be determined from the vendor and product IDs in ``std_board_info``.

Troubleshooting
===============

Device Not Discovered
---------------------

If the device doesn't appear in ``openstack accelerator device list``:

1. Verify the device is visible in the VM:

   .. code-block:: console

      $ lspci -nn | grep -i non-volatile

2. Check that the vendor/product IDs in ``local.conf`` match ``lspci`` output

3. Verify the PCI driver is enabled:

   .. code-block:: console

      $ sudo grep -i "enabled_drivers" /etc/cyborg/cyborg.conf
      enabled_drivers = fake_driver,pci_driver

4. Check Cyborg agent logs:

   .. code-block:: console

      $ sudo journalctl -u devstack@cyborg-agent | grep -i pci

5. Restart Cyborg services:

   .. code-block:: console

      $ sudo systemctl restart devstack@cyborg-agent

References
==========

* :doc:`/contributor/devstack_setup` - DevStack setup guide
* :doc:`/contributor/vm-setup` - VM creation guide
* :doc:`/contributor/driver-development-guide` - Driver development guide
* `Nova PCI Passthrough <https://docs.openstack.org/nova/latest/admin/pci-passthrough.html>`_
* `QEMU NVMe Device Documentation <https://qemu.readthedocs.io/en/latest/system/devices/nvme.html>`_
* `NVMe Specification <https://nvmexpress.org/specifications/>`_
