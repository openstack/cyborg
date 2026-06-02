.. _pci-sim-developer-guide:

=======================
pci-sim developer guide
=======================

``pci-sim`` is a small Linux kernel module that lets Cyborg, Nova,
libvirt, QEMU, and CI jobs exercise SR-IOV PCI passthrough flows without
requiring physical SR-IOV hardware. The module is intentionally a test
fixture. It creates fake PCI host bridges, exposes one fake physical
function (PF) per bridge, creates software virtual functions (VFs), gives
those devices IOMMU groups, and provides a VFIO path that QEMU can assign
to a guest.

This guide is written for Cyborg maintainers and contributors who are
comfortable with Python, OpenStack, Linux, and virtualization concepts, but
who may not have worked on kernel modules, the PCI core, IOMMU drivers,
VFIO, or the TTY subsystem before.

The goal is to explain enough kernel background to understand why the module
works, how the pieces fit together, and how to extend and test it safely.
It is not a replacement for the Linux kernel documentation, the QEMU manual,
or the Cyborg DevStack plugin documentation. It focuses on the subset of
those systems that ``pci-sim`` uses.

How to read this guide
======================

This document is both a learning path and a maintainer reference.

A good first pass for a new maintainer is:

#. Read `What pci-sim is and is not`_ and `Core mental model`_.
#. Read `Kernel concepts used by pci-sim`_ before reading the C source.
#. Build the module with `Build and local test workflow`_.
#. Run the host loopback test, then the QEMU/VFIO smoke test.
#. Read `Source map`_ and `Lifecycle and data flows`_ with the source open.
#. Use `Extension workflows`_ when planning changes.
#. Use `Troubleshooting`_ when local tests fail.

Existing focused pages remain useful:

* :doc:`overview` is the short overview.
* :doc:`build` is the concise build command reference.
* :doc:`kernel-dependencies` lists required kernel options.
* :doc:`testing` lists local, QEMU, and DevStack test commands.
* :doc:`devstack` documents DevStack plugin integration.
* :doc:`migration-plan` records future live-migration work.

What pci-sim is and is not
==========================

``fake_pci_sriov.ko`` is a fake PCI SR-IOV and VFIO test fixture. It is
useful when the thing under test is the control plane:

* Does the host discover PCI devices?
* Does ``sriov_numvfs`` create VFs?
* Does each VF have an IOMMU group?
* Can a VF bind to a VFIO driver?
* Can QEMU start with the VF assigned?
* Can an unmodified guest see and use the assigned PCI function?
* Can Cyborg and Nova consume a passthrough-like PCI resource in a local
  development environment?

It is not real accelerator hardware and it is not a production security
boundary. The fake IOMMU provides enough IOMMU API behavior for VFIO tests,
but there is no hardware DMA engine and no real DMA remapping. The fake BARs
and UART are small software models designed for smoke testing, not complete
device emulation.

The module deliberately models only a small topology:

* up to 16 fake PCI host bridges,
* one PF per fake host bridge,
* one root bus per PF,
* bus 0, slot 0 only,
* PF at function 0,
* up to seven VFs at functions 1 through 7.

That topology is enough for Cyborg and Nova passthrough workflows while
keeping the module small enough to maintain in the Cyborg repository.

Core mental model
=================

At a high level the flow is:

.. code-block:: text

   pci-sim source + running-kernel headers
           |
           v
   fake_pci_sriov.ko
           |
           v
   fake PCI host bridge(s)
           |
           v
   fake PF(s) with SR-IOV capability
           |
           v
   echo N > /sys/bus/pci/devices/<PF>/sriov_numvfs
           |
           v
   fake VF pci_dev objects
           |
           +--> pci_sim_loopback_vf
           |        |
           |        v
           |   /dev/ttyPCI_SIM<N> host loopback
           |
           +--> driver_override=pci_sim_vfio_pci
                    |
                    v
                VFIO device for QEMU
                    |
                    v
                guest-visible 16550-style UART loopback

The important idea is that ``pci-sim`` does not ask userspace to invent PCI
devices. It makes the kernel PCI core discover fake devices by creating a
fake PCI host bridge and providing custom PCI config-space operations. Once
those fake devices are normal kernel ``struct pci_dev`` objects, the rest of
the kernel can interact with them through normal PCI, SR-IOV, IOMMU, VFIO,
TTY, and sysfs paths.

There are two VF use modes:

Host loopback mode
  The normal VF driver, ``pci_sim_loopback_vf``, binds to fake VFs and
  creates ``/dev/ttyPCI_SIM<N>``. A host process writes bytes to that TTY
  and reads the same bytes back. This validates that the PF/VF creation and
  host-side driver path work.

VFIO guest mode
  A script or developer unbinds the VF from the host loopback driver, writes
  ``pci_sim_vfio_pci`` to ``driver_override``, and binds the VF to the
  override-only VFIO driver. QEMU assigns the VF to a guest. The VFIO
  driver traps BAR0 reads and writes and emulates a small 16550-style UART so
  a guest can verify the device is usable.

The two modes are mutually exclusive for a given VF. When VFIO guest mode is
active, the kernel does not create ``/dev/ttyPCI_SIM<N>`` on the host for that
VF because the VF is owned by the VFIO driver. Inside the guest the
8250-compatible driver names the device ``/dev/ttyS<N>`` rather than
``/dev/ttyPCI_SIM<N>``. Data written and read inside the guest loops back
inside the guest only; there is no host-to-guest data bridge.

Kernel concepts used by pci-sim
===============================

PCI devices, functions, and config space
----------------------------------------

PCI identifies functions by domain, bus, device, and function number. Linux
normally learns that topology from firmware and hardware. Each PCI function
has configuration space containing the vendor ID, device ID, class, command
bits, BAR registers, capability pointers, and optional extended capabilities.

``pci-sim`` creates a fake root bus and answers config-space reads itself.
The PCI core probes bus 0, slot 0, function 0 and sees the fake PF because
``fake_pci_read_config()`` returns a valid vendor/device ID for that function.
When VFs are enabled, the same config-space path starts returning valid data
for functions 1 through 7.

Config space is important because most of the rest of the system is driven by
what it advertises:

* vendor/device IDs decide which PCI drivers can bind,
* the class code influences how tools and guests describe the device,
* BAR registers describe MMIO regions,
* the PCIe capability makes the device look like a PCIe endpoint,
* the SR-IOV extended capability lets the PCI SR-IOV core create VFs.

BARs, MMIO, and resources
-------------------------

A PCI BAR describes an address range where a driver can access device
registers or memory. For real hardware, a BAR maps to device MMIO. Drivers
normally request and map that resource, then use MMIO accessors to program
the device.

``pci-sim`` has no real device MMIO. It still advertises BARs so the PCI
core, sysfs, VFIO, QEMU, Nova, and Cyborg see a realistic PCI resource model.
For normal PCI enumeration, BAR sizing is handled in config-space writes. For
VFIO guest access, BAR0 is not mmapable; the custom VFIO driver traps VFIO
read/write operations and emulates the UART registers in software.

This difference is deliberate and important. Generic ``vfio-pci`` expects a
real BAR behind the PCI device. ``pci-sim`` uses ``pci_sim_vfio_pci`` because
BAR0 must be interpreted by software rather than mapped directly.

PCI host bridges and ``pci_ops``
--------------------------------

A PCI host bridge connects a CPU/root complex to a PCI bus. In normal systems,
firmware and platform code describe host bridges and their config-space access
method. In ``pci-sim``, the module creates synthetic host bridges with
``pci_alloc_host_bridge()`` and ``pci_host_probe()``.

The key callback table is ``struct pci_ops``. ``pci-sim`` installs
``fake_pci_ops`` on each fake bridge. The PCI core calls those callbacks
when it wants to read or write config space. This is the mechanism that
turns an in-memory ``struct fake_pci_device`` into something the PCI core can
discover as a real ``struct pci_dev``.

Each fake host bridge owns:

* a PCI domain number,
* a bus resource,
* a memory window resource,
* one fake PF config-space image,
* up to seven fake VF config-space images.

SR-IOV PFs, VFs, and ``sriov_numvfs``
-------------------------------------

SR-IOV lets one physical device expose lightweight virtual functions. The
physical function is the PF. The virtual functions are VFs. Linux exposes
standard sysfs controls such as ``sriov_totalvfs`` and ``sriov_numvfs`` for a
PF that advertises SR-IOV support and has a PF driver with an
``sriov_configure`` callback.

The normal user-visible operation is:

.. code-block:: console

   $ echo 4 | sudo tee /sys/bus/pci/devices/<PF>/sriov_numvfs

For ``pci-sim``, that write calls the fake PF driver's
``fake_pci_sriov_configure()`` callback. The callback creates or removes the
software VF config-space images and calls ``pci_enable_sriov()`` or
``pci_disable_sriov()`` so the PCI core performs its normal VF enumeration and
removal work.

This design matters because it uses the same SR-IOV sysfs and PCI core flow
that real PF drivers use. Cyborg and Nova therefore exercise realistic host
control-plane behavior even though the devices are fake.

IOMMU groups and domains
------------------------

VFIO depends on IOMMU isolation. The IOMMU group is the unit of ownership:
all devices in a group must be safe for one userspace owner before VFIO can
expose them. On real hardware, grouping depends on PCIe topology, ACS,
aliases, and platform IOMMU behavior.

``pci-sim`` registers a small software IOMMU. It claims only devices on the
fake PCI domains and returns one generic IOMMU group per fake PCI device. That
is intentionally friendly to assignment tests: each fake VF can be assigned
individually.

The fake IOMMU also implements paging-domain callbacks and tracks map/unmap
state in an xarray. This is enough for VFIO and IOMMUFD paths that expect an
IOMMU driver to exist, but it is not real DMA translation. The fake devices do
not perform DMA.

VFIO and ``vfio-pci-core``
--------------------------

VFIO exposes devices to userspace in a controlled way. QEMU uses VFIO when it
assigns a PCI device to a guest. For PCI devices, the generic driver is
``vfio-pci``. The kernel also provides ``vfio-pci-core`` as a library for
variant drivers that need device-specific behavior while reusing the common
VFIO PCI implementation.

``pci-sim`` uses a VFIO PCI variant driver named ``pci_sim_vfio_pci``. It
reuses ``vfio-pci-core`` for the normal VFIO PCI machinery and overrides the
parts that must be fake-device aware:

* BAR0 region information,
* BAR0 read/write handling,
* BAR0 mmap rejection,
* optional guest config-space identity overlay.

The ID table uses ``PCI_DRIVER_OVERRIDE_DEVICE_VFIO``. That makes the driver
an override-only VFIO driver. It should not bind to every matching VF by
default. A test explicitly selects it with ``driver_override``.

``driver_override`` and sysfs binding
-------------------------------------

``driver_override`` is a PCI sysfs attribute. Writing a driver name to it
restricts driver matching for that device to the named driver. It does not
load the driver, unbind the current driver, or bind the new driver by itself.

The safe manual flow is:

.. code-block:: console

   $ sudo modprobe vfio-pci
   $ echo <VF> | sudo tee /sys/bus/pci/devices/<VF>/driver/unbind
   $ echo pci_sim_vfio_pci | \
       sudo tee /sys/bus/pci/devices/<VF>/driver_override
   $ echo <VF> | sudo tee /sys/bus/pci/drivers_probe

The helper scripts perform this flow for the QEMU and CirrOS smoke tests.

TTY, serial, and 16550 UARTs
----------------------------

The host loopback path uses the kernel TTY layer directly. A TTY driver owns
one or more ``tty_port`` objects and registers device nodes such as
``/dev/ttyPCI_SIM0``. Data received by a TTY driver is pushed through the
TTY flip buffer so readers see it through the normal character-device path.

``pci-sim`` also implements a small 16550-style UART model. A 16550 UART is a
classic serial port programming interface with byte-sized registers such as
THR/RBR, IER, IIR, LCR, MCR, LSR, MSR, and SCR. Linux guests commonly have
8250/16550 drivers, so a tiny UART loopback is a convenient payload for
proving that a passed-through PCI function is visible and usable.

The same UART helper functions are used by two separate owners:

* the host TTY VF driver,
* the VFIO guest BAR0 emulator.

Each owner has its own UART state.

Kernel modules, kbuild, and Kconfig
-----------------------------------

``pci-sim`` is built as an out-of-tree kernel module. It is not part of the
Cyborg Python package. The build uses the kernel build system from the
running kernel headers, usually through ``/lib/modules/$(uname -r)/build``.

The local ``Kconfig`` records the in-tree-style dependencies that would be
needed if the module lived in the kernel tree:

* ``PCI``
* ``PCI_DOMAINS``
* ``IOMMU_API``
* ``VFIO_PCI_CORE``
* ``TTY``

The repository helper ``tools/check-kernel-config.sh`` checks the running
kernel configuration before a local build/test cycle.

Why this approach works
=======================

The design works because it uses normal kernel subsystem entry points instead
of bypassing them.

The PCI core accepts fake devices
---------------------------------

The module creates a host bridge and installs ``fake_pci_ops``. During
``pci_host_probe()``, the PCI core scans the fake root bus. When it reads
config space for bus 0, slot 0, function 0, ``fake_pci_ops`` returns the fake
PF's config-space bytes. The PCI core therefore creates a normal ``pci_dev``
for the PF.

Once the PF exists as a normal ``pci_dev``, normal PCI driver binding applies.
The fake PF driver binds by vendor/device ID and provides the SR-IOV callback.

The SR-IOV core accepts fake VFs
--------------------------------

The PF advertises an SR-IOV extended capability. When a user writes
``sriov_numvfs``, the PCI SR-IOV core calls the PF driver's
``sriov_configure`` callback. ``pci-sim`` marks the corresponding fake VF
config-space images present and then calls ``pci_enable_sriov()``.

The PCI core then scans the VF functions based on the SR-IOV capability's VF
layout fields. Reads for functions 1 through 7 now return valid config-space
bytes, so the VFs become normal ``pci_dev`` objects too.

VFIO accepts the fake VFs
-------------------------

VFIO needs assignable devices to have IOMMU groups. The fake IOMMU claims the
fake PCI domains and returns an IOMMU group for each fake device. This gives
VFIO the group and domain structure it expects.

Because the VFs are real kernel ``pci_dev`` objects and have IOMMU groups,
VFIO can expose them through a VFIO PCI driver.

QEMU can use the fake VF
------------------------

QEMU does not need to know that the host bridge is fake. It opens the VFIO
device, queries regions, and issues reads and writes through the VFIO API.

The custom VFIO driver is the compatibility layer between QEMU's expectation
of a VFIO PCI device and the module's lack of real MMIO. For BAR0, it reports
a software region and services read/write requests by calling the UART model.
It rejects BAR0 mmap so userspace cannot bypass the emulation path.

Guests can use the assigned function
------------------------------------

In compatibility mode, the VFIO driver overlays guest config-space reads so
the guest sees a serial-class, 8250-compatible identity. That lets an
unmodified guest bind an existing serial driver instead of requiring a custom
guest driver for the fake Cyborg IDs.

The guest writes a byte to the UART transmit register through MMIO. QEMU
translates that into a VFIO BAR0 write. ``pci_sim_vfio_pci`` traps the write
and stores the byte in the UART FIFO. When the guest reads the receive
register and line-status register, the VFIO driver returns data from that same
FIFO. This proves that the assigned VF is visible and usable inside the
guest.

Build and local test workflow
=============================

This section explains what happens when you build the module locally. The
short command reference is in :doc:`build`; this section explains the
mechanics.

The Makefile
------------

The module Makefile is a kbuild wrapper:

.. code-block:: make

   obj-m += fake_pci_sriov.o
   fake_pci_sriov-y := \
       fake_pci_sriov_core.o \
       fake_pci_sriov_cfg.o \
       fake_pci_sriov_iommu.o \
       fake_pci_sriov_uart.o \
       fake_pci_sriov_vfio.o

``obj-m`` tells kbuild to build ``fake_pci_sriov`` as a loadable module.
The ``fake_pci_sriov-y`` line tells kbuild that the final module is a
composite object assembled from several source files. The source split is for
maintainability; the kernel still loads one module, ``fake_pci_sriov.ko``.

The wrapper variables are:

``KDIR``
  Defaults to ``/lib/modules/$(uname -r)/build``. This is the build tree or
  header package for the running kernel.

``PWD``
  Set to the current ``pci-sim`` directory. It is passed to kbuild as
  ``M=$(PWD)``.

``M=$(PWD)``
  Tells kbuild this is an external module directory. kbuild reads the local
  Makefile, builds the listed objects, and writes kernel-module build outputs
  next to the sources.

The main targets are:

``all`` / ``modules``
  Build ``fake_pci_sriov.ko``.

``clean``
  Remove kernel build outputs from ``pci-sim/``.

``install`` / ``modules_install``
  Install the module into the running kernel's module tree and run
  ``depmod -a``.

``check-kernel-config``
  Run ``../tools/check-kernel-config.sh``.

Local build flow
----------------

Install a compiler and headers for the running kernel, then check the kernel
configuration:

.. code-block:: console

   $ sudo apt install linux-headers-$(uname -r) build-essential
   $ bash tools/check-kernel-config.sh

Build from the Cyborg repository root:

.. code-block:: console

   $ make -C pci-sim modules

Or run the equivalent external-module command directly:

.. code-block:: console

   $ make -C /lib/modules/$(uname -r)/build M=$PWD/pci-sim modules

The output module is:

.. code-block:: text

   pci-sim/fake_pci_sriov.ko

If you are testing against a different kernel tree, override ``KDIR``:

.. code-block:: console

   $ make -C pci-sim KDIR=/path/to/linux/build modules

Local load and host smoke test
------------------------------

For a standalone ``insmod`` workflow, preload VFIO PCI support first. This is
needed because ``insmod`` does not resolve module dependencies the way
``modprobe`` does.

.. code-block:: console

   $ sudo modprobe vfio-pci
   $ sudo insmod pci-sim/fake_pci_sriov.ko

Then run the host loopback smoke test:

.. code-block:: console

   $ sudo pci-sim/test_pci_sim_loopback.py

The test finds the fake PF, writes ``sriov_numvfs``, waits for
``/dev/ttyPCI_SIM*``, writes bytes to the TTY, and verifies that the same bytes
are read back.

Clean up after manual testing:

.. code-block:: console

   $ sudo pci-sim/cleanup_fake_pci_sriov.sh

QEMU/VFIO smoke test
--------------------

The QEMU smoke helper builds the expected VFIO binding flow around the module:

.. code-block:: console

   $ make -C pci-sim modules
   $ MODULE=./pci-sim/fake_pci_sriov.ko \
       pci-sim/run_fake_pci_qemu_vfio_smoke.sh

The helper loads the module, enables a VF, unbinds any current VF driver,
sets ``driver_override`` to ``pci_sim_vfio_pci``, probes the driver, and starts
QEMU with ``-device vfio-pci,host=<VF>``.

CirrOS guest helpers perform deeper guest-level checks. See :doc:`testing`
for the current command reference.

Validation by change type
-------------------------

Use the smallest test that proves the area you changed, then run broader tests
before proposing the change for review.

.. list-table:: Suggested validation
   :header-rows: 1

   * - Change area
     - Minimum validation
   * - Makefile or build compatibility
     - ``make -C pci-sim clean modules`` and ``bash tools/check-kernel-config.sh``
   * - Module parameters or host creation
     - host loopback test and multi-PF smoke test
   * - PCI config space, IDs, BARs, or SR-IOV capability
     - host loopback test, ``lspci -vv``, and QEMU/VFIO smoke test
   * - IOMMU behavior
     - verify ``/sys/kernel/iommu_groups`` links and run QEMU/VFIO smoke test
   * - TTY or UART host path
     - ``sudo pci-sim/test_pci_sim_loopback.py``
   * - VFIO BAR0 or guest identity
     - QEMU/VFIO smoke test and CirrOS guest UART test
   * - DevStack-facing behavior
     - local smoke tests first, then the DevStack serial echo test from
       :doc:`testing`

Source map
==========

``pci-sim/Makefile``
  Out-of-tree kbuild wrapper. Defines the composite module and delegates to
  the running kernel build tree.

``pci-sim/Kconfig``
  In-tree-style dependency declaration and help text. Useful when comparing
  the module with the upstream kernel sample or checking required kernel
  features.

``pci-sim/fake_pci_sriov.h``
  Shared internal header. Defines device IDs, topology constants, BAR sizes,
  UART constants, shared structs, extern globals, and cross-file prototypes.

``pci-sim/fake_pci_sriov_compat.h``
  Kernel API compatibility gates. IOMMU and VFIO callback tables change over
  time, so version-specific decisions are kept here instead of scattered
  through the module.

``pci-sim/fake_pci_sriov_core.c``
  Module parameters, global fake host list, resource allocation, host bridge
  creation/removal, module init, and module exit.

``pci-sim/fake_pci_sriov_cfg.c``
  Fake PCI config-space helpers, PCIe capability setup, SR-IOV capability
  setup, custom ``pci_ops``, PF driver, and ``sriov_configure`` callback.

``pci-sim/fake_pci_sriov_iommu.c``
  Software IOMMU implementation. Claims fake PCI domains, creates groups, and
  tracks fake IOVA mappings.

``pci-sim/fake_pci_sriov_uart.c``
  Shared UART model, host TTY driver, host VF loopback PCI driver, and
  ``/dev/ttyPCI_SIM<N>`` creation.

``pci-sim/fake_pci_sriov_vfio.c``
  Override-only VFIO PCI variant. Reuses ``vfio-pci-core`` and emulates BAR0
  UART access for QEMU/guest tests.

``pci-sim/test_pci_sim_loopback.py``
  Host loopback smoke test.

``pci-sim/run_fake_pci_multi_pf_smoke.sh``
  Multi-PF and cleanup smoke test.

``pci-sim/run_fake_pci_qemu_vfio_smoke.sh``
  QEMU/VFIO smoke test.

CirrOS guest helper scripts
  ``pci-sim/run_cirros_vfio_guest_probe.sh`` and
  ``pci-sim/run_cirros_vfio_userdata_echo.sh`` provide guest-level probes for
  the assigned VF and UART echo path.

``pci-sim/cleanup_fake_pci_sriov.sh``
  Cleanup helper for VFs, overrides, and module unload.

Lifecycle and data flows
========================

Module load order
-----------------

The init path is ordered so that dependencies exist before devices appear:

#. Validate module parameters such as ``num_pfs``.
#. Register the fake IOMMU platform device.
#. Add the IOMMU sysfs object and register ``fake_iommu_ops``.
#. Register the TTY driver.
#. Register the override-only VFIO PCI driver.
#. Register the normal VF host loopback driver.
#. Register the PF driver.
#. Allocate each fake host and register its platform device.
#. Create each PCI host bridge and call ``pci_host_probe()``.

Drivers are registered before fake hosts are probed so that newly discovered
PFs and VFs can bind immediately through the normal driver model.

Module unload order
-------------------

Unload runs in the reverse direction:

#. Remove fake host bridges first. This removes PF/VF ``pci_dev`` objects
   while the PCI drivers still exist.
#. Unregister the PF, VF, and VFIO PCI drivers.
#. Unregister the TTY driver.
#. Unregister the fake IOMMU and its platform device.

The reverse-order cleanup pattern is a normal kernel convention. If an init
step succeeds, the error path and exit path must undo it in an order that does
not leave live objects pointing at unregistered callbacks.

PF and VF creation
------------------

The PF config-space image is initialized before the host bridge is probed.
The PF advertises the fake vendor/device IDs, a BAR, PCIe endpoint capability,
and SR-IOV capability.

VFs start as not present. When a user writes a positive value to
``sriov_numvfs``, the PF driver's ``sriov_configure`` callback initializes the
requested VF config-space images and calls ``pci_enable_sriov()``. The PCI
core then scans the VF functions and creates normal ``pci_dev`` objects.

When ``sriov_numvfs`` is written with ``0``, the PF driver calls
``pci_disable_sriov()`` and marks all VFs not present.

IOMMU group creation
--------------------

The fake IOMMU is registered before fake PCI devices are created. When the
IOMMU core probes devices, ``fake_iommu_probe_device()`` accepts only PCI
devices whose domain belongs to a fake host. ``fake_iommu_device_group()``
returns a generic group for each fake device.

This gives each fake PF and VF a sysfs group under
``/sys/kernel/iommu_groups``. VFIO uses those groups to decide whether a VF
can be assigned.

Host loopback flow
------------------

In host loopback mode:

#. A VF appears as a normal ``pci_dev``.
#. ``pci_sim_loopback_vf`` binds by vendor/device ID.
#. The driver enables the PCI device.
#. It allocates a ``pci_sim_vf_tty`` object.
#. It allocates an ID and registers ``/dev/ttyPCI_SIM<N>``.
#. A host process writes bytes to the TTY.
#. The TTY ``write`` operation stores bytes in the UART FIFO.
#. The driver pushes those bytes back through the TTY flip buffer.
#. The host process reads the same bytes back.

VFIO guest UART flow
--------------------

In VFIO guest mode:

#. A script creates at least one VF.
#. It unbinds the VF from any current host driver.
#. It writes ``pci_sim_vfio_pci`` to the VF's ``driver_override``.
#. It triggers driver probe.
#. ``pci_sim_vfio_pci`` allocates and registers a VFIO PCI core device.
#. QEMU opens the VFIO device.
#. QEMU queries config space and BAR regions.
#. The VFIO driver overlays guest config space in compatibility mode.
#. QEMU assigns the VF to the guest.
#. Guest UART MMIO accesses become VFIO BAR0 reads and writes.
#. The VFIO driver services those reads and writes from the software UART.

Kernel references and design influences
=======================================

``pci-sim`` uses standard PCI, SR-IOV, IOMMU, VFIO, TTY, sysfs, and kbuild
interfaces. The fake PCI host bridge and SR-IOV topology are specific to this
module; there was not a pre-existing kernel sample that already provided the
same fake PCI SR-IOV device model.

``mtty`` VFIO mediated-device sample
------------------------------------

The useful VFIO-emulated-serial reference, relative to the Linux kernel
source root, is ``samples/vfio-mdev/mtty.c``.

``mtty`` shows how an emulated serial device can be exposed to userspace via
VFIO and used by QEMU as a PCI-like device. It is valuable for understanding
VFIO regions, UART register emulation, and future migration ideas.

However, ``mtty`` is mediated-device based. It does not create SR-IOV VFs
behind a fake PCI host bridge. ``pci-sim`` creates real kernel ``pci_dev``
objects and uses a fake IOMMU so the host control plane sees PCI/SR-IOV/VFIO
objects that look much closer to passthrough hardware.

Useful kernel documentation
---------------------------

When maintaining this module, the most useful local kernel references are:

* ``Documentation/PCI/pci.rst`` for PCI driver vocabulary.
* ``Documentation/PCI/pci-iov-howto.rst`` for SR-IOV concepts and
  ``sriov_numvfs``.
* ``Documentation/PCI/sysfs-pci.rst`` for PCI sysfs resource files.
* ``Documentation/ABI/testing/sysfs-bus-pci`` for binding, ``driver_override``,
  and SR-IOV sysfs attributes.
* ``Documentation/ABI/testing/sysfs-kernel-iommu_groups`` for IOMMU group
  sysfs layout.
* ``Documentation/driver-api/vfio.rst`` for VFIO groups, devices, regions,
  and IOMMUFD context.
* ``Documentation/driver-api/vfio-pci-device-specific-driver-acceptance.rst``
  for why ``vfio-pci-core`` variant drivers exist.
* ``Documentation/driver-api/tty/tty_driver.rst`` and
  ``Documentation/driver-api/tty/tty_port.rst`` for TTY driver structure.
* ``Documentation/kbuild/modules.rst`` for external module builds.

For host bridge, ``pci_ops``, SR-IOV internals, IOMMU callback signatures, and
VFIO callback tables, source files and headers are often more authoritative
than prose docs because these APIs change over time.

Kernel maintenance conventions used here
========================================

Keep ownership local
--------------------

Each source file owns one major subsystem. Keep new code near the subsystem
that owns the state:

* host lifetime in ``fake_pci_sriov_core.c``,
* config space and SR-IOV in ``fake_pci_sriov_cfg.c``,
* IOMMU callbacks in ``fake_pci_sriov_iommu.c``,
* UART/TTY logic in ``fake_pci_sriov_uart.c``,
* VFIO logic in ``fake_pci_sriov_vfio.c``.

If a helper must be shared, declare it in ``fake_pci_sriov.h`` and keep the
owning implementation in one source file.

Preserve init and unwind symmetry
---------------------------------

Kernel init paths often have many partial-success states. When adding a new
registration step, add the matching cleanup in:

* the normal module exit path,
* every error path after the new step can succeed.

Cleanup should run in reverse registration order.

Use the right lock for the data
-------------------------------

The module uses several synchronization primitives:

``fake_hosts_lock``
  Protects the global host list.

``host->lock``
  Protects per-host VF enable/disable state.

UART spinlock
  Protects UART registers and FIFO state, including paths that should not
  sleep.

TTY state mutex
  Protects per-VF TTY lifetime state such as the ``dead`` flag.

Do not hold locks across calls that may sleep unless the lock type allows it.
When changing locking, consider whether the path can run from sysfs, driver
probe/remove, VFIO read/write, or TTY operations.

Respect refcounts and lifetimes
-------------------------------

TTY ports, VFIO devices, PCI devices, and platform devices all have lifetime
rules. The source uses helpers such as ``tty_port_get()``, ``tty_port_put()``,
``vfio_put_device()``, ``pci_set_drvdata()``, and platform-device unregister
paths to keep those lifetimes explicit.

When extending the module, prefer existing subsystem helpers over ad-hoc object
lifetime handling.

Keep compatibility gates centralized
------------------------------------

IOMMU and VFIO APIs change between kernel versions. The compatibility header
exists so callback-shape decisions are visible in one place. If a new kernel
requires a version-specific callback, add the gate there and keep the main
source readable.

Use kernel logging style
------------------------

Kernel code should use delayed formatting through ``pr_*()``, ``dev_*()``, or
``pci_*()`` helpers rather than building formatted strings separately. Include
enough context in errors for a maintainer to identify the failing host, device,
or subsystem.

Extension workflows
===================

Change module parameters
------------------------

Likely files:

* ``fake_pci_sriov_core.c``
* ``fake_pci_sriov.h`` if other files need the value
* this guide or :doc:`build` if behavior is user-visible

Checklist:

#. Choose a safe default.
#. Decide whether the parameter can change after load.
#. Add ``module_param`` and ``MODULE_PARM_DESC``.
#. Validate the value during module init if invalid values can break topology.
#. Add local build and at least host loopback validation.

Change PCI IDs, classes, or config-space layout
-----------------------------------------------

Likely files:

* ``fake_pci_sriov.h``
* ``fake_pci_sriov_cfg.c``
* ``fake_pci_sriov_vfio.c`` if guest-visible identity changes
* helper scripts that match IDs
* DevStack sample/config only if OpenStack matching changes

Checklist:

#. Decide whether the change is host-visible, guest-visible, or both.
#. Update PF/VF config-space initialization.
#. Check ``lspci -nn -D`` and ``lspci -vv`` output.
#. Run host loopback and QEMU/VFIO smoke tests.
#. If Cyborg or Nova matching changes, run the DevStack serial echo test.

Add BAR behavior
----------------

Likely files:

* ``fake_pci_sriov_cfg.c`` for config-space BAR sizing and flags
* ``fake_pci_sriov_vfio.c`` for VFIO region behavior
* ``fake_pci_sriov.h`` for constants

Checklist:

#. Decide whether the BAR is only host-visible metadata or guest-accessible.
#. Keep config-space BAR size and VFIO region-info behavior consistent unless
   there is a documented compatibility reason.
#. If guest access is needed, decide whether mmap can be safe. BAR0 currently
   rejects mmap so all accesses are trapped.
#. Add tests that prove QEMU uses the intended path.

Extend UART behavior
--------------------

Likely files:

* ``fake_pci_sriov_uart.c``
* ``fake_pci_sriov_vfio.c`` if VFIO BAR offsets change

Checklist:

#. Keep common UART behavior in shared helpers.
#. Preserve the distinction between host TTY UART state and VFIO UART state.
#. Add host TTY tests for host behavior.
#. Add QEMU/CirrOS tests for guest behavior.

Add interrupt support
---------------------

Today the UART model exposes status bits but does not inject a full guest UART
interrupt path. Adding that support would likely touch:

* UART interrupt state,
* VFIO IRQ information or eventfd triggering,
* optional INTx/MSI modeling,
* guest tests that avoid polling-only assumptions.

This is more than a small UART-register change. Plan it as a separate feature
with focused tests.

Add migration support
---------------------

The current migration plan is in :doc:`migration-plan`. The fake VF state is
small enough to serialize: UART registers, FIFO contents, and a few line-state
flags. The difficult part is integrating that state with the current VFIO PCI
migration APIs in a way QEMU and libvirt can use.

Treat migration as a VFIO feature, not just a UART helper change.

Update kernel API compatibility
-------------------------------

Likely files:

* ``fake_pci_sriov_compat.h``
* whichever IOMMU or VFIO source file uses the changed callback

Checklist:

#. Identify the exact kernel version where the callback changed.
#. Add a named compatibility macro.
#. Keep the main code paths readable.
#. Build against the oldest and newest intended kernels if possible.
#. Run at least host loopback and QEMU/VFIO smoke tests.

Troubleshooting
===============

Module does not build
---------------------

Check that headers for the running kernel are installed and that the configured
kernel has the required options:

.. code-block:: console

   $ bash tools/check-kernel-config.sh
   $ make -C pci-sim clean modules

If the error is an unknown IOMMU or VFIO callback, check
``fake_pci_sriov_compat.h`` first. The local kernel may have an API shape that
is newer or older than the current gates.

Module does not load
--------------------

Check kernel logs:

.. code-block:: console

   $ sudo dmesg | tail -100

Common causes include missing dependency modules, invalid module parameters,
or failure to allocate a fake MMIO window. For standalone ``insmod``, preload
VFIO PCI support:

.. code-block:: console

   $ sudo modprobe vfio-pci

PF does not appear in lspci
---------------------------

Check whether the module loaded successfully and whether a fake host bridge was
created:

.. code-block:: console

   $ lspci -D -d 1d55:1000
   $ sudo dmesg | grep fake_pci

If no PF appears, focus on module init, host bridge creation, resource
allocation, and ``pci_host_probe()`` errors.

Writing sriov_numvfs fails
--------------------------

Find the PF and inspect its SR-IOV files:

.. code-block:: console

   $ PF=$(lspci -D -d 1d55:1000 | awk 'NR==1 {print $1}')
   $ ls /sys/bus/pci/devices/$PF/sriov_*
   $ cat /sys/bus/pci/devices/$PF/sriov_totalvfs

The fake PF supports at most seven VFs. The driver rejects changing directly
from one non-zero VF count to another; disable VFs first:

.. code-block:: console

   $ echo 0 | sudo tee /sys/bus/pci/devices/$PF/sriov_numvfs
   $ echo 4 | sudo tee /sys/bus/pci/devices/$PF/sriov_numvfs

No /dev/ttyPCI_SIM device appears
---------------------------------

Check whether VFs exist and which driver owns them:

.. code-block:: console

   $ lspci -D -d 1d55:1001
   $ for dev in /sys/bus/pci/devices/*; do \
       [ -e "$dev/vendor" ] || continue; \
       [ "$(cat $dev/vendor)" = "0x1d55" ] || continue; \
       echo "$dev -> $(readlink -f $dev/driver 2>/dev/null || echo none)"; \
     done

If a VF is bound to ``pci_sim_vfio_pci``, it will not create a host TTY. Clear
``driver_override`` and re-probe or rerun the cleanup helper.

No IOMMU group appears
----------------------

Check the VF sysfs link:

.. code-block:: console

   $ readlink /sys/bus/pci/devices/<VF>/iommu_group

If it is missing, the fake IOMMU did not claim the device. Check that the
IOMMU was registered before host bridge probing and that the device is on one
of the fake PCI domains.

VF binds to the wrong driver
----------------------------

For host loopback, the VF should bind to ``pci_sim_loopback_vf``. For guest
assignment, it should bind to ``pci_sim_vfio_pci``.

Remember that ``driver_override`` does not do the bind by itself. The usual
VFIO sequence is unbind, set override, then probe:

.. code-block:: console

   $ echo <VF> | sudo tee /sys/bus/pci/devices/<VF>/driver/unbind
   $ echo pci_sim_vfio_pci | \
       sudo tee /sys/bus/pci/devices/<VF>/driver_override
   $ echo <VF> | sudo tee /sys/bus/pci/drivers_probe

QEMU fails with VFIO errors
---------------------------

Check:

* the VF has an IOMMU group,
* the VF is bound to ``pci_sim_vfio_pci``,
* ``vfio-pci`` support is loaded,
* the process has permission to access VFIO devices,
* nested virtualization environments may need unsafe interrupt settings as
  documented in :doc:`devstack`.

Guest sees no usable serial device
----------------------------------

Check whether ``vfio_guest_8250_compat`` is enabled. In compatibility mode,
the VFIO driver overlays guest config-space reads so the guest sees an
8250-compatible serial identity. Without compatibility mode, the guest may
need manual probing or a different test method.

Also remember that BAR0 mmap is intentionally rejected. Guest access should go
through QEMU's VFIO read/write path.

rmmod fails or cleanup leaves devices behind
--------------------------------------------

Disable VFs and clear overrides before unloading:

.. code-block:: console

   $ sudo pci-sim/cleanup_fake_pci_sriov.sh

Open TTYs, running QEMU processes, bound VFIO devices, or still-enabled VFs can
hold references that prevent clean unload.

Limitations and future work
===========================

Current limitations are intentional unless a future change explicitly extends
the model:

* The IOMMU is a software test fixture, not real DMA remapping.
* The topology has one slot per root bus and at most seven VFs per PF.
* BAR/MMIO behavior is synthetic.
* Generic ``vfio-pci`` is not enough for guest UART tests; use
  ``pci_sim_vfio_pci``.
* Host TTY loopback and guest VFIO UART loopback are separate paths.
* UART interrupt injection is not a complete guest interrupt model today.
* Live migration support is future work; see :doc:`migration-plan`.

Related reading
===============

In this repository:

* :doc:`overview`
* :doc:`build`
* :doc:`kernel-dependencies`
* :doc:`testing`
* :doc:`devstack`
* :doc:`migration-plan`

In a local Linux checkout, useful starting points include:

* ``Documentation/PCI/pci.rst``
* ``Documentation/PCI/pci-iov-howto.rst``
* ``Documentation/PCI/sysfs-pci.rst``
* ``Documentation/driver-api/vfio.rst``
* ``Documentation/driver-api/tty/tty_driver.rst``
* ``Documentation/kbuild/modules.rst``
* ``samples/vfio-mdev/mtty.c``
