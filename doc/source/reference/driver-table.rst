.. list-table:: Driver Support
   :widths: 20 20 30 30
   :header-rows: 1

   * - Driver Name
     - Supported Products
     - Description
     - Notes
   * - Fake Driver
     - None
     - A driver that creates a fake device with accelerator resources of type FPGA. Useful for exploring Cyborg without hardware and for Continuous Integration testing.
     - None
   * - Intel FPGA OPAE Driver
     - `Intel PAC <https://www.intel.com/content/www/us/en/programmable/products/boards_and_kits/dev-kits/altera/acceleration-card-arria-10-gx/overview.html>`_
     - The driver for Intel FPGA devices with OPAE software stack.
     - Supports programming of FPGA bitstreams of type ``gbs``.
   * - Nvidia GPU driver
     - None
     - The driver for Nvidia GPUs.
     - None
   * - Ascend AI Chip driver
     - None
     - The driver for Huawei's Ascend AI chips.
     - None
