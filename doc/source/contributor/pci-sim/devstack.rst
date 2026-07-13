========
DevStack
========

pci-sim is built into the Cyborg DevStack plugin. To enable it, assign each
PF a personality and an owning service in ``PCI_SIM_SERVICE_MAP``:

.. code-block:: ini

   enable_plugin cyborg https://opendev.org/openstack/cyborg

   PCI_SIM_SERVICE_MAP=0:uart:nova,1:uart:cyborg

A ready-to-use sample configuration is provided in the Cyborg repository at
``devstack/local-conf.pci-sim.sample``.

Plugin settings
===============

``PCI_SIM_BUILD``
  Build and install the module during the DevStack ``install`` phase.
  Defaults to ``True``.

``PCI_SIM_LOAD``
  Load ``fake_pci_sriov`` after building it.  Defaults to ``True``.

``PCI_SIM_ALLOW_UNSAFE_INTERRUPTS``
  Allow VFIO on hosts without interrupt remapping support by setting
  ``vfio_iommu_type1.allow_unsafe_interrupts`` before probing the fake VFs.
  Defaults to ``True`` for nested/devstack test environments.

``PCI_SIM_NUM_VFS``
  Number of virtual functions to enable on each ``uart`` PF (``0`` through
  ``7``, default ``4``). This count does not select the personality.

``PCI_SIM_SERVICE_MAP``
  An empty or unset map disables pci-sim (the default). A nonempty map
  enables pci-sim and creates one PF per entry. For example, to create two
  PFs, set this in ``local.conf``::

    PCI_SIM_SERVICE_MAP=0:uart:nova,1:mdev:cyborg

  Nova receives the UART VFs from PF0 and Cyborg manages the mdev parent on
  PF1. Use one ``index:personality:service`` entry per configured PF, separated
  by commas without spaces. Indices must be consecutive starting at zero,
  with at most 16 PFs. PF0 has the lowest PCI address; the entries themselves
  may appear in any order. Supported assignments are ``uart:nova``,
  ``uart:cyborg`` and ``mdev:cyborg``.

  For ``uart:nova``, the plugin writes Nova's ``[pci] device_spec`` and
  ``alias`` options using exact VF addresses and ``managed="no"``. For
  ``uart:cyborg``, it enables Cyborg's ``pci_driver`` and adds the VF
  addresses to ``[pci] passthrough_whitelist``.

``PCI_SIM_MDEV_TYPE``
  The type Cyborg configures on each ``mdev:cyborg`` parent. Defaults to
  ``fake_pci_sriov_pf-sim_accel_small``.

``PCI_SIM_MDEV_INSTANCES``
  Maximum number of small-type mdev instances per ``mdev:cyborg`` PF.
  Set this to a positive integer (default ``8``). The large-type limit is
  one quarter of this value, rounded down, with a minimum of one. With the
  default setting, each parent advertises 8 small or 2 large instances.

``PCI_SIM_NOVA_PCI_IN_PLACEMENT``
  When Nova PCI configuration is enabled, configure
  ``[pci] report_in_placement`` and
  ``[filter_scheduler] pci_in_placement``.  Defaults to ``True``.

``PCI_SIM_CREATE_TEST_FLAVORS``
  Create convenience test resources during ``stack/test-config``.  Defaults to
  ``True``.  When Nova PCI configuration is enabled, the plugin creates a
  flavor named by ``PCI_SIM_NOVA_FLAVOR_NAME`` with
  ``pci_passthrough:alias``.  When
  Cyborg PCI configuration is enabled, the plugin creates a Cyborg device
  profile named by ``PCI_SIM_CYBORG_DEVICE_PROFILE_NAME`` and a flavor named by
  ``PCI_SIM_CYBORG_FLAVOR_NAME`` with ``accel:device_profile``.

``PCI_SIM_MODULE_ARGS``
  Optional extra arguments passed to ``modprobe fake_pci_sriov`` when
  ``PCI_SIM_LOAD=True``. Do not include ``num_pfs`` here; the plugin derives
  it from ``PCI_SIM_SERVICE_MAP``.
