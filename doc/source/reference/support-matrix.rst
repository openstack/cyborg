=====================
Cyborg Support Matrix
=====================

Cyborg supports specific operations on VMs with attached accelerator
resources, which are generally a subset of the full set of VM operations
supported by Nova (`nova-vm-ops
<https://docs.openstack.org/api-guide/compute/server_concepts.html>`__).

In this release, these operations have a dependency on specific Nova
patches (`nova-patches
<https://review.opendev.org/#/q/status:open+project:openstack/nova+bp/nova-cyborg-interaction>`__).
They can be expected to work in Cyborg only
if and when these Nova patches get merged without significant changes.
These operations are not supported in this release since the dependencies
are not met.

.. list-table:: VM Operations Expected to Work With Nova Dependencies
   :header-rows: 1

   * - VM Operation
     - Command
   * - VM creation
     - ``openstack server create``
   * - VM deletion
     - ``openstack server delete``
   * - Reboot within VM
     - ``ssh to VM and reboot in OS``
   * - Soft reboot
     - ``openstack server reboot --soft``
   * - Pause/Unpause
     - ``openstack server pause``, ``openstack server unpause``
   * - Backup
     - ``openstack server backup create``
   * - Take a snapshot
     - ``openstack server image create``
   * - Lock/Unlock
     - ``openstack server lock``, ``openstack server unlock``
   * - Rebuild/Evacuate
     - ``openstack server rebuild``
   * - Shelve/Unshelve
     - ``openstack server shelve``, ``openstack server unshelve``

Operations not listed here may or may not work.

Driver Support
~~~~~~~~~~~~~~

The list of drivers available as part of the Cyborg distribution
at the time of release can be found in the
``[project.entry-points."cyborg.accelerator.driver"]`` section of
`Cyborg's pyproject.toml
<https://opendev.org/openstack/cyborg/src/branch/master/pyproject.toml>`__

The following table provides additional information for individual drivers.

.. list-table:: Driver Support
   :widths: 15 30 10 15 30
   :header-rows: 1

   * - Name
     - Description
     - Testing
     - Documentation
     - Status
   * - Fake Driver
     - A driver that creates a fake device with accelerator resources of type FPGA. Useful for exploring Cyborg without hardware and for Continuous Integration testing.
     - CI
     - `Partial <../configuration/drivers.html#fake-driver>`__
     - **Supported**
   * - Intel FPGA OPAE Driver
     - The driver for Intel FPGA devices with OPAE software stack.
     - Missing
     - `Partial <../configuration/drivers.html#fpga-drivers>`__
     - **Experimental**

       Supported products: `Intel PAC <https://www.intel.com/content/www/us/en/programmable/products/boards_and_kits/dev-kits/altera/acceleration-card-arria-10-gx/overview.html>`__. Supports programming of FPGA bitstreams of type ``gbs``.
   * - Nvidia GPU driver
     - The driver for Nvidia GPUs.
     - Missing
     - `Partial <../configuration/drivers.html#nvidia-gpu-driver>`__
     - **Experimental**
   * - Ascend AI Chip driver
     - The driver for Huawei's Ascend AI chips.
     - Missing
     - `Partial <../configuration/drivers.html#huawei-ascend-driver>`__
     - **Experimental**
   * - Intel QAT Driver
     - The driver for Intel QAT Cards.
     - Missing
     - `Partial <../configuration/drivers.html#intel-qat-driver>`__
     - **Experimental**

       Supported products: `Intel QuickAssist Technology Card <https://www.intel.com/content/www/us/en/architecture-and-technology/intel-quick-assist-technology-overview.html>`__
   * - Inspur FPGA Driver
     - The driver for Inspur FPGA Cards.
     - Missing
     - `Partial <../configuration/drivers.html#fpga-drivers>`__
     - **Experimental**
   * - Intel NIC Driver
     - The driver for Intel NIC Cards. Supports SR-IOV VF discovery and passthrough via Cyborg + Nova + Neutron smartNIC flow.
     - Missing
     - `Partial <../configuration/drivers.html#intel-nic-driver>`__
     - **Experimental**

       Supported products: `Intel X710 10GbE SFP+ <https://www.intel.com/content/www/us/en/products/details/ethernet/700-network-adapters.html>`__, `Intel XXV710 25GbE SFP28 <https://www.intel.com/content/www/us/en/products/details/ethernet/700-network-adapters.html>`__, Intel XXV710 25GbE backplane. Requires SR-IOV to be enabled on the NIC and IOMMU on the host. Uses ``i40e`` host driver and ``iavf`` guest driver.
   * - Inspur NVMe SSD Driver
     - The driver for Inspur NVMe SSD DISK.
     - Missing
     - `Partial <../configuration/drivers.html#inspur-nvme-ssd-driver>`__
     - **Experimental**
   * - Xilinx FPGA Driver
     - The driver for Xilinx FPGA Cards.
     - Missing
     - `Partial <../configuration/drivers.html#fpga-drivers>`__
     - **Experimental**
   * - SPDK NVMe-oF Driver
     - The SPDK NVMe over Fabrics driver.
     - Missing
     - `Partial <../configuration/drivers.html>`__
     - **Experimental**
   * - PCI Driver
     - Generic PCI device driver for accelerator discovery via PCI whitelist.
     - CI
     - `Partial <../configuration/drivers.html#generic-pci-driver>`__
     - **Supported**
