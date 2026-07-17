.. list-table:: Driver Support
   :widths: 20 20 30 30 30
   :header-rows: 1

   * - Driver Name
     - Supported Products
     - Description
     - Notes
     - Temporary Test Report
   * - Fake Driver
     - None
     - A driver that creates a fake device with accelerator resources of type FPGA. Useful for exploring Cyborg without hardware and for Continuous Integration testing.
     - None
     - None
   * - Intel FPGA OPAE Driver
     - `Intel PAC <https://www.intel.com/content/www/us/en/programmable/products/boards_and_kits/dev-kits/altera/acceleration-card-arria-10-gx/overview.html>`_
     - The driver for Intel FPGA devices with OPAE software stack.
     - Supports programming of FPGA bitstreams of type ``gbs``.
     - None
   * - Nvidia GPU driver
     - None
     - The driver for Nvidia GPUs.
     - None
     - None
   * - Ascend AI Chip driver
     - None
     - The driver for Huawei's Ascend AI chips.
     - None
     - None
   * - Intel QAT Driver
     - `Intel QuickAssist Technology Card <https://www.intel.com/content/www/us/en/architecture-and-technology/intel-quick-assist-technology-overview.html>`_
     - The driver for Intel QAT Cards.
     - None
     - Test results reported at Aug 2020. Please reference: `Intel QAT Driver Test Report <https://wiki.openstack.org/wiki/Cyborg/TestReport/IntelQAT>`_
   * - Inspur FPGA Driver
     - None
     - The driver for Inspur FPGA Cards.
     - None
     - Test results reported at Aug 2020. Please reference: `Inspur FPGA Driver Test Report <https://wiki.openstack.org/wiki/Cyborg/TestReport/InspurFPGA>`_
   * - Intel NIC Driver
     - `Intel X710 10GbE SFP+ <https://www.intel.com/content/www/us/en/products/details/ethernet/700-network-adapters.html>`_, `Intel XXV710 25GbE SFP28 <https://www.intel.com/content/www/us/en/products/details/ethernet/700-network-adapters.html>`_, Intel XXV710 25GbE backplane
     - The driver for Intel NIC Cards. Supports SR-IOV VF discovery and passthrough via Cyborg + Nova + Neutron smartNIC flow.
     - Requires SR-IOV to be enabled on the NIC and IOMMU on the host. Uses ``i40e`` host driver and ``iavf`` guest driver.
     - Test results reported at Feb 2021. Please reference: `Intel NIC Driver Test Report <https://wiki.openstack.org/wiki/Cyborg/TestReport/IntelNic>`_
   * - Inspur NVMe SSD Driver
     - None
     - The driver for Inspur NVMe SSD DISK.
     - None
     - Test results reported at Feb 2021. Please reference: `Inspur NVMe SSD Driver Test Report <https://wiki.openstack.org/wiki/Cyborg/TestReport/InspurNVMeSSD>`_
   * - Xilinx FPGA Driver
     - None
     - The driver for Xilinx FPGA Cards.
     - None
     - None

.. note:: Temporary Test Report: This is a temporary test report, it is only
     valid for a short time, if you encounter problems, please contact the
     `Cyborg team <https://review.opendev.org/#/admin/groups/1243,members>`_.
