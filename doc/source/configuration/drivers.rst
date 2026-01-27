==================================
Accelerator Driver Configuration
==================================

This document describes how to configure accelerator drivers in Cyborg.
The Cyborg agent discovers and manages hardware accelerators through
pluggable drivers that are enabled via configuration.

Enabling Drivers
================

Drivers are enabled in the ``[agent]`` section of ``cyborg.conf`` using the
``enabled_drivers`` option. This is a comma-separated list of driver names.

.. code-block:: ini

    [agent]
    enabled_drivers = intel_fpga_driver, nvidia_gpu_driver

The driver names correspond to entry points defined in the Cyborg package.
Only enabled drivers will be loaded by the cyborg-agent service.

Available Drivers
=================

The following table lists all available drivers and their supported hardware:

.. list-table:: Available Accelerator Drivers
   :widths: 25 15 20 40
   :header-rows: 1

   * - Driver Name
     - Vendor ID
     - Product ID
     - Description
   * - ``intel_fpga_driver``
     - ``0x8086``
     - ``0x09c4``
     - Intel FPGA (PAC Arria10)
   * - ``inspur_fpga_driver``
     - ``0x1bd4``
     - (auto-detect)
     - Inspur FPGA cards
   * - ``xilinx_fpga_driver``
     - ``0x10ee``
     - (auto-detect)
     - Xilinx FPGA cards
   * - ``nvidia_gpu_driver``
     - ``0x10de``
     - (auto-detect)
     - NVIDIA GPUs with optional vGPU support
   * - ``intel_nic_driver``
     - ``0x8086``
     - ``0x158b``, ``0x1572``
     - Intel NIC X710 series
   * - ``intel_qat_driver``
     - ``0x8086``
     - ``0x37c8``
     - Intel QuickAssist Technology
   * - ``inspur_nvme_ssd_driver``
     - ``0x1bd4``
     - (auto-detect)
     - Inspur NVMe SSD
   * - ``huawei_ascend_driver``
     - ``0x19e5``
     - ``0xd100``
     - Huawei Ascend AI chips
   * - ``pci_driver``
     - (configurable)
     - (configurable)
     - Generic PCI passthrough driver
   * - ``fake_driver``
     - ``0xABCD``
     - ``0xabcd``
     - Fake driver for testing

Driver Configuration Reference
==============================

FPGA Drivers
------------

The FPGA drivers (``intel_fpga_driver``, ``xilinx_fpga_driver``,
``inspur_fpga_driver``) automatically discover FPGA devices on the host
by scanning PCI devices matching their vendor IDs. No additional
configuration is required beyond enabling the driver.

**Intel FPGA Driver**

The Intel FPGA driver discovers devices via ``/sys/class/fpga`` and
``/sys/bus/pci/devices``. It supports programming bitstreams using
``fpgaconf``.

.. code-block:: ini

    [agent]
    enabled_drivers = intel_fpga_driver

**Xilinx FPGA Driver**

The Xilinx FPGA driver uses ``lspci`` to discover Xilinx devices and
supports programming via the Xilinx Runtime (XRT) tools.

.. code-block:: ini

    [agent]
    enabled_drivers = xilinx_fpga_driver

**Inspur FPGA Driver**

The Inspur FPGA driver discovers Inspur FPGA cards via ``lspci``.

.. code-block:: ini

    [agent]
    enabled_drivers = inspur_fpga_driver

NVIDIA GPU Driver
-----------------

The NVIDIA GPU driver supports both physical GPUs (pGPUs) and virtual GPUs
(vGPUs). For vGPU support, additional configuration is required to map
vGPU types to physical GPU PCI addresses.

**Basic GPU Configuration (pGPU only)**

For physical GPU passthrough without vGPU:

.. code-block:: ini

    [agent]
    enabled_drivers = nvidia_gpu_driver

**vGPU Configuration**

To enable vGPU support, configure the ``[gpu_devices]`` section with the
vGPU types you want to enable. Each vGPU type requires a corresponding
``[vgpu_<type>]`` section that specifies which physical GPUs should
provide that vGPU type.

.. code-block:: ini

    [agent]
    enabled_drivers = nvidia_gpu_driver

    [gpu_devices]
    # List of vGPU types to enable on this compute node
    # These names correspond to mdev types (e.g., nvidia-35, nvidia-36)
    enabled_vgpu_types = nvidia-35, nvidia-36

    # Configuration for nvidia-35 vGPU type
    [vgpu_nvidia-35]
    # PCI addresses of physical GPUs that will provide this vGPU type
    device_addresses = 0000:84:00.0,0000:85:00.0

    # Configuration for nvidia-36 vGPU type
    [vgpu_nvidia-36]
    device_addresses = 0000:86:00.0

.. note::

    Each physical GPU can only be configured for one vGPU type. If the
    same PCI address is specified for multiple vGPU types, the cyborg-agent
    will raise an ``InvalidGPUConfig`` exception.

Intel NIC Driver
----------------

The Intel NIC driver supports Intel X710 series network interface cards.
It provides configuration options for mapping physical networks to
interfaces and mapping network functions to specific interfaces.

.. code-block:: ini

    [agent]
    enabled_drivers = intel_nic_driver

    [nic_devices]
    # List of NIC configuration profiles to enable
    enabled_nic_types = x710_static

    # Configuration for the x710_static profile
    [x710_static]
    # Map physical networks to interface names
    # Format: <physical_network>:<interface1>|<interface2>
    physical_device_mappings = physnet1:eth2|eth3

    # Map network functions to interface names
    # Format: <function_name>:<interface1>|<interface2>
    function_device_mappings = GTPv1:eth3|eth2

**Configuration Options**

``physical_device_mappings``
    Maps OpenStack physical network names to NIC interface names.
    Multiple interfaces can be specified using the pipe (``|``) separator.

``function_device_mappings``
    Maps network function names to NIC interface names for specialized
    network processing functions.

Intel QAT Driver
----------------

The Intel QAT (QuickAssist Technology) driver discovers Intel QAT devices
automatically. No additional configuration is required.

.. code-block:: ini

    [agent]
    enabled_drivers = intel_qat_driver

Inspur NVMe SSD Driver
----------------------

The Inspur NVMe SSD driver discovers Inspur NVMe storage devices
automatically via ``lspci``.

.. code-block:: ini

    [agent]
    enabled_drivers = inspur_nvme_ssd_driver

Huawei Ascend Driver
--------------------

The Huawei Ascend driver discovers Huawei Ascend AI accelerator chips
automatically.

.. code-block:: ini

    [agent]
    enabled_drivers = huawei_ascend_driver

Generic PCI Driver
------------------

The generic PCI driver (``pci_driver``) allows passthrough of arbitrary
PCI devices that match a configurable whitelist. This is useful for
devices that don't have a dedicated Cyborg driver.

**Whitelist Configuration**

The ``[pci]`` section contains a ``passthrough_whitelist`` option that
specifies which PCI devices can be managed by Cyborg. The whitelist uses
JSON format and supports several matching methods.

**Match by Vendor and Product ID**

.. code-block:: ini

    [agent]
    enabled_drivers = pci_driver

    [pci]
    # Match devices with specific vendor and product IDs
    passthrough_whitelist = {"vendor_id":"8086", "product_id":"1520"}

**Match by PCI Address (Glob Style)**

Use glob-style patterns to match PCI addresses. The address format is
``domain:bus:slot.function``.

.. code-block:: ini

    [pci]
    # Match all functions on bus 0a, slot 00
    passthrough_whitelist = {"address":"*:0a:00.*"}

    # Match a specific device
    passthrough_whitelist = {"address":"0000:0b:00.0"}

**Match by PCI Address (Regex Style)**

Use regex patterns for more complex address matching:

.. code-block:: ini

    [pci]
    # Match devices on bus 02, slot 01, functions 0-2
    passthrough_whitelist = {"address": {"domain": ".*", "bus": "02", "slot": "01", "function": "[0-2]"}}

**Multiple Whitelist Entries**

You can specify multiple whitelist entries to match different device types:

.. code-block:: ini

    [pci]
    passthrough_whitelist = {"vendor_id":"8086", "product_id":"1520"}
    passthrough_whitelist = {"vendor_id":"10de", "product_id":"1eb8"}
    passthrough_whitelist = {"address":"*:0c:00.*"}

**Match by Device Name**

You can also match by network interface name (for NIC devices):

.. code-block:: ini

    [pci]
    passthrough_whitelist = {"devname":"eth0"}

Fake Driver
-----------

The fake driver creates simulated accelerator resources for testing
purposes. It does not require any actual hardware.

.. code-block:: ini

    [agent]
    enabled_drivers = fake_driver

Complete Configuration Examples
===============================

Example 1: Intel FPGA Deployment
--------------------------------

A minimal configuration for Intel FPGA acceleration:

.. code-block:: ini

    [DEFAULT]
    transport_url = rabbit://stackrabbit:secret@controller:5672/
    debug = True

    [database]
    connection = mysql+pymysql://cyborg:secret@controller/cyborg

    [agent]
    enabled_drivers = intel_fpga_driver

    [keystone_authtoken]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = cyborg
    password = secret
    project_domain_name = Default
    user_domain_name = Default

    [placement]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = placement
    password = secret
    project_domain_name = Default
    user_domain_name = Default

Example 2: NVIDIA GPU with vGPU
-------------------------------

Configuration for NVIDIA GPU with multiple vGPU types:

.. code-block:: ini

    [DEFAULT]
    transport_url = rabbit://stackrabbit:secret@controller:5672/
    debug = True

    [database]
    connection = mysql+pymysql://cyborg:secret@controller/cyborg

    [agent]
    enabled_drivers = nvidia_gpu_driver

    [gpu_devices]
    enabled_vgpu_types = nvidia-35, nvidia-36, nvidia-37

    [vgpu_nvidia-35]
    # Assign nvidia-35 type to GPUs on slot 84 and 85
    device_addresses = 0000:84:00.0,0000:85:00.0

    [vgpu_nvidia-36]
    # Assign nvidia-36 type to GPU on slot 86
    device_addresses = 0000:86:00.0

    [vgpu_nvidia-37]
    # Assign nvidia-37 type to GPU on slot 87
    device_addresses = 0000:87:00.0

    [keystone_authtoken]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = cyborg
    password = secret
    project_domain_name = Default
    user_domain_name = Default

    [placement]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = placement
    password = secret
    project_domain_name = Default
    user_domain_name = Default

Example 3: Intel NIC with Network Mappings
------------------------------------------

Configuration for Intel NIC with physical network mappings:

.. code-block:: ini

    [DEFAULT]
    transport_url = rabbit://stackrabbit:secret@controller:5672/
    debug = True

    [database]
    connection = mysql+pymysql://cyborg:secret@controller/cyborg

    [agent]
    enabled_drivers = intel_nic_driver

    [nic_devices]
    enabled_nic_types = x710_static

    [x710_static]
    # Map physnet1 to eth2 and eth3 interfaces
    physical_device_mappings = physnet1:eth2|eth3
    # Map GTPv1 function to eth3 and eth2
    function_device_mappings = GTPv1:eth3|eth2

    [keystone_authtoken]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = cyborg
    password = secret
    project_domain_name = Default
    user_domain_name = Default

    [placement]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = placement
    password = secret
    project_domain_name = Default
    user_domain_name = Default

Example 4: Generic PCI Passthrough
----------------------------------

Configuration for generic PCI device passthrough:

.. code-block:: ini

    [DEFAULT]
    transport_url = rabbit://stackrabbit:secret@controller:5672/
    debug = True

    [database]
    connection = mysql+pymysql://cyborg:secret@controller/cyborg

    [agent]
    enabled_drivers = pci_driver

    [pci]
    # Allow Intel I350 NICs
    passthrough_whitelist = {"vendor_id":"8086", "product_id":"1521"}
    # Allow all devices on bus 0c
    passthrough_whitelist = {"address":"*:0c:*.*"}

    [keystone_authtoken]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = cyborg
    password = secret
    project_domain_name = Default
    user_domain_name = Default

    [placement]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = placement
    password = secret
    project_domain_name = Default
    user_domain_name = Default

Example 5: Multi-Driver Deployment
----------------------------------

Configuration enabling multiple accelerator types on a single compute node:

.. code-block:: ini

    [DEFAULT]
    transport_url = rabbit://stackrabbit:secret@controller:5672/
    debug = True

    [database]
    connection = mysql+pymysql://cyborg:secret@controller/cyborg

    [agent]
    # Enable multiple drivers
    enabled_drivers = intel_fpga_driver, nvidia_gpu_driver, intel_qat_driver

    # GPU vGPU configuration
    [gpu_devices]
    enabled_vgpu_types = nvidia-35

    [vgpu_nvidia-35]
    device_addresses = 0000:84:00.0

    [keystone_authtoken]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = cyborg
    password = secret
    project_domain_name = Default
    user_domain_name = Default

    [placement]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = placement
    password = secret
    project_domain_name = Default
    user_domain_name = Default

    [nova]
    auth_url = http://controller:5000
    auth_type = password
    project_name = service
    username = nova
    password = secret
    project_domain_name = Default
    user_domain_name = Default

Discovering PCI Devices
=======================

To identify PCI devices on your system for configuration, use the ``lspci``
command:

.. code-block:: bash

    # List all PCI devices with vendor and product IDs
    lspci -nn

    # List devices with full PCI addresses
    lspci -nn -D

    # Filter for specific device types
    lspci -nn | grep -i nvidia
    lspci -nn | grep -i fpga

The output shows the PCI address in ``domain:bus:slot.function`` format
along with vendor and product IDs in brackets (e.g., ``[8086:1520]``).

Troubleshooting
===============

**Driver not loading**

Verify the driver name is correctly spelled in ``enabled_drivers`` and
matches an entry point in the Cyborg package.

**Devices not discovered**

Check that:

- The hardware is properly installed and recognized by the OS (``lspci``)
- The correct driver is enabled
- For the PCI driver, the ``passthrough_whitelist`` matches your devices

**vGPU configuration errors**

Ensure that:

- Each PCI address is only assigned to one vGPU type
- The vGPU type names match those available on your NVIDIA GPU
- The ``[vgpu_<type>]`` section names include the ``vgpu_`` prefix
