==================================
Generic Mdev Driver Configuration
==================================

The generic mdev (mediated device) driver (``mdev_driver``) allows
Cyborg to discover and manage mdev-capable devices such as NVIDIA
vGPUs, Intel GVT-g virtual GPUs, and other hardware that exposes
the Linux kernel mdev interface.  It reports these devices to
Placement so that Nova can schedule instances with accelerator
resources.

Prerequisites
=============

Before enabling the generic mdev driver, ensure that:

* The Linux kernel supports mediated devices
  (``CONFIG_VFIO_MDEV`` or equivalent).
* One or more mdev-capable devices are installed and their host
  drivers are loaded (e.g. the NVIDIA vGPU manager or the
  ``i915`` driver with GVT-g support).
* Each parent device exposes ``mdev_supported_types`` in sysfs.
  Verify by checking that the path
  ``/sys/class/mdev_bus/<PCI_ADDRESS>/mdev_supported_types/``
  exists and contains one or more type directories.

.. code-block:: console

    $ ls /sys/class/mdev_bus/
    0000:06:00.0  0000:07:00.0

    $ ls /sys/class/mdev_bus/0000:06:00.0/mdev_supported_types/
    nvidia-319  nvidia-320

Enabling the driver
===================

Add ``mdev_driver`` to the ``enabled_drivers`` list in the
``[agent]`` section of ``cyborg.conf``:

.. code-block:: ini

    [agent]
    enabled_drivers = mdev_driver

Then configure the ``[mdev]`` section as described below and
restart the ``cyborg-agent`` service.

Configuration options
=====================

All mdev driver options live in the ``[mdev]`` section of
``cyborg.conf``.  The ``device_spec`` option is multi-valued;
each value is a JSON object describing a class of mdev devices
to discover.  A value may also be a JSON array of such
objects, which is convenient when generating the configuration
with templates.  The following keys are supported:

``address`` (required)
    PCI address of the parent device, e.g. ``"0000:06:00.0"``.
    Use ``"*"`` to match all mdev-capable parent devices.

``mdev_type`` (required)
    The mdev type name as it appears in
    ``mdev_supported_types/``, e.g. ``"nvidia-319"``.

``max_instances`` (optional)
    Integer cap on the number of instances reported to Placement
    for this device/type combination.

``resource_class`` (optional)
    Custom Placement resource class name.  If omitted, a default
    is derived automatically as ``CUSTOM_MDEV_<TYPE_NAME>``
    (with hyphens replaced by underscores, uppercased).

``traits`` (optional)
    A list of additional Placement trait strings to set on the
    resource provider.

Configuration examples
======================

NVIDIA vGPU example
-------------------

Expose a single GPU as vGPU type ``nvidia-319``:

.. code-block:: ini

    [mdev]
    device_spec = {"address": "0000:06:00.0", "mdev_type": "nvidia-319"}

Intel GVT-g example
-------------------

Expose an Intel integrated GPU for GVT-g with a custom resource
class and trait:

.. code-block:: ini

    [mdev]
    device_spec = {"address": "0000:00:02.0", "mdev_type": "i915-GVTg_V5_4", "resource_class": "CUSTOM_INTEL_GVTG", "traits": ["CUSTOM_INTEL_GVTG_V5_4"]}

Wildcard matching
-----------------

Match all parent devices for an mdev type, capping each at
8 instances:

.. code-block:: ini

    [mdev]
    device_spec = {"address": "*", "mdev_type": "generic-mdev-type", "max_instances": 8}

Multiple entries
----------------

Multiple ``device_spec`` lines can target different devices or
types with independent settings.  When a device/type pair matches
more than one entry, the first match wins.

A PCI address can only be configured with a single
mdev type.  Configuring the same ``address`` with different
``mdev_type`` values is a fatal configuration error that prevents
the agent from starting.  The ``"*"`` wildcard address is exempt
from this rule, so specific and wildcard entries may use
different types.  Note, however, that most hardware (e.g. NVIDIA
vGPUs) only supports one active mdev type per parent device, so
configurations that match several types to the same parent are
only valid for devices that actually support it.

.. code-block:: ini

    [mdev]
    device_spec = {"address": "0000:06:00.0", "mdev_type": "nvidia-319", "max_instances": 4}
    device_spec = {"address": "*", "mdev_type": "nvidia-320", "max_instances": 16}

In this example the GPU at ``0000:06:00.0`` with type
``nvidia-319`` is capped at 4 instances, while every other
device that has type nvidia-320 is capped at 16.

Array form
----------

Instead of repeating the ``device_spec`` option, a single value
can hold a JSON array of objects.  This form produces the same
configuration as repeating the option once per object and is
convenient when the configuration file is generated from
templates:

.. code-block:: ini

    [mdev]
    device_spec = [{"address": "0000:06:00.0", "mdev_type": "nvidia-319", "max_instances": 4}, {"address": "*", "mdev_type": "nvidia-320", "max_instances": 16}]

Both forms can be mixed in the same configuration.

Coexistence with vendor-specific drivers
=========================================

.. warning::

    Do **not** enable both the generic mdev driver
    (``mdev_driver``) and a vendor-specific driver (e.g.
    ``nvidia_gpu_driver``) for the same parent device.

Troubleshooting
===============

mdev_bus sysfs path does not exist
-----------------------------------

If the agent log shows::

    WARNING ... mdev_bus sysfs path does not exist: /sys/class/mdev_bus

the kernel does not have mdev support loaded.  Verify that the
required kernel modules are loaded (e.g. ``mdev``, ``vfio_mdev``,
or the vendor-specific host driver).

mdev_supported_types not found for a device
--------------------------------------------

The log message::

    WARNING ... mdev_supported_types path does not exist for device ...

means the parent device driver is loaded but has not registered
any mdev types.  Check that the vendor host driver is the correct
version and that the device firmware supports mediated device
creation.

Invalid device_spec JSON
-------------------------

If the agent fails to start with an error like::

    Invalid mdev device_spec ...

the ``device_spec`` value is not valid JSON.  Each entry must be
a single-line JSON object.  Common mistakes include using single
quotes instead of double quotes, or omitting required keys
(``address`` and ``mdev_type``).

No devices discovered
---------------------

If the agent starts successfully but no mdev resources appear
in Placement:

1. Verify that ``mdev_driver`` is listed in
   ``[agent] enabled_drivers``.
2. Confirm that at least one ``device_spec`` entry is present
   in the ``[mdev]`` section.
3. Check that the ``address`` and ``mdev_type`` values match
   what is available in sysfs.
4. Look for log messages at INFO level from the mdev driver
   indicating how many parent devices and types were discovered.
