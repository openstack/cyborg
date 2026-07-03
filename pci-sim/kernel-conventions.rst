.. SPDX-License-Identifier: GPL-2.0-only

Kernel conventions for pci-sim
==============================

This document defines the local coding conventions and validation checks for
``pci-sim``.  ``pci-sim`` is an out-of-tree kernel module, but it should be
written and reviewed like Linux kernel code so that it remains maintainable and
can track upstream PCI, SR-IOV, VFIO, IOMMU, and TTY APIs.

The Linux kernel documentation and nearby subsystem code are the source of
truth.  In particular, consult:

* ``Documentation/process/coding-style.rst``
* ``Documentation/process/submit-checklist.rst``
* ``Documentation/process/submitting-patches.rst``
* ``Documentation/dev-tools/checkpatch.rst``
* ``Documentation/dev-tools/clang-format.rst``
* ``Documentation/PCI/pci.rst``
* ``Documentation/PCI/pci-iov-howto.rst``
* ``Documentation/driver-api/vfio.rst``

Required local checks
---------------------

Run these before posting or merging pci-sim changes.

Build the module
~~~~~~~~~~~~~~~~

From ``pci-sim/``::

   make test-build
   make clean

The build must complete without new warnings.  Run ``make clean`` before
finishing local validation so generated module artifacts are not left behind.

Run lint
~~~~~~~~

Run the local pci-sim lint target against the diff from ``origin/master``::

   make lint

``make lint`` runs the repo-supported style checks for normal review: the
vendored Linux ``checkpatch.pl`` in patch mode with ``--no-spelling`` and
``git clang-format`` for C and header changes.  The format check updates the
working tree when formatting changes are needed, then fails so the developer
can review and include those formatting updates.  The local ``.clang-format``
copy is tuned to reduce immediate post-``(" line breaks, but lint still
ignores ``OPEN_ENDED_LINE`` because ``clang-format`` can produce that
checkpatch advisory for long module metadata macros.  It also ignores
``CONSTANT_COMPARISON`` and
``LINUX_VERSION_CODE`` for the isolated out-of-tree compatibility header,
``EMBEDDED_FILENAME`` for the Makefile lint path list, and
``FILE_PATH_CHANGES`` because pci-sim ownership is tracked by the Cyborg
repository rather than the Linux kernel ``MAINTAINERS`` file.  Spelling is
handled by the repository's top-level ``codespell`` pre-commit hook, not by
checkpatch.

``checkpatch.pl`` is a guide, not an absolute authority.  New errors should be
fixed.  New warnings and checks should either be fixed or explicitly justified
in review.

The local lint target runs ``checkpatch.pl`` with ``--no-tree``.  That keeps
the check self-contained and avoids extra Linux-tree helper
dependencies, but it means complete SPDX expression validation is not part of
the initial lint gate.

Run full checks
~~~~~~~~~~~~~~~

Before posting pci-sim changes, run::

   make check

``make check`` runs ``make lint`` and then builds the module with the kernel
``W=1`` extra-warning level.  It cleans generated module artifacts after the
build.

Run behavior tests for behavior changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For changes that affect runtime behavior, run the relevant smoke tests, for
example::

   make test-loopback
   make test-multi-pf

Also run the VFIO, QEMU, or CirrOS helper tests when touching those paths.
A style-clean build is not sufficient for PCI, VFIO, or IOMMU behavior
changes.

Formatter policy
----------------

``clang-format`` is useful, but formatting churn must be controlled.

* A one-time normalization with ``clang-format`` is acceptable if it is a
  dedicated formatting-only change.
* Use the ``.clang-format`` file provided in this repository. It was
  imported from the Linux kernel formatting configuration so contributors do
  not need a separate Linux kernel checkout.
* Review the resulting diff manually for correctness and readability.  The
  imported ``.clang-format`` approximates kernel style but is not perfect.
* Do not mix formatting-only churn with functional changes.
* After any normalization commit, format only new or touched code.
* Prefer the repository ``clang-format`` output for pci-sim formatting.  The
  goal is close alignment with kernel style, but consistent automated
  formatting is more important than preserving hand-aligned exceptions.
* Do not use ``scripts/Lindent`` as an automated formatter for pci-sim.

Developer coding conventions
----------------------------

General kernel style
~~~~~~~~~~~~~~~~~~~~

* Use tabs for indentation.  Kernel indentation is 8 columns.
* Prefer 80-column lines.  Do not split user-visible log strings solely to fit
  the limit because that makes them harder to grep.
* Use normal kernel brace style: opening braces stay on the control statement
  line, while function opening braces go on the next line.
* Use lower-case names with underscores.  Global symbols should be descriptive;
  local variables can be short when the scope is small.
* Avoid typedefs for structs and pointers.
* Prefer inline functions over macros when type checking or single evaluation
  matters.  Keep macros for constants, compile-time constructs, and cases where
  an inline function cannot work.
* Include the header that directly declares the API being used.  Do not rely on
  unrelated headers to include it indirectly.
* Keep functions short, focused, and shallowly indented.  Split functions that
  mix setup, emulation, cleanup, and policy decisions.
* Use direct returns when no cleanup is required.  Use ``goto`` cleanup labels
  for multi-step allocation or registration paths, and name labels after the
  cleanup they perform.
* Comments should explain purpose, constraints, hardware behavior, locking,
  ordering, or ABI.  Do not restate obvious code.
* Document every module parameter with ``MODULE_PARM_DESC()``.

pci-sim structure
~~~~~~~~~~~~~~~~~

* Keep subsystem ownership clear.  PCI config-space emulation, host bridge
  setup, IOMMU grouping, VFIO behavior, UART emulation, polling threads, and
  tests should remain separated by responsibility.
* Avoid compatibility sprawl.  If kernel-version compatibility is required,
  isolate it in compatibility helpers or headers and keep normal code readable.
* Avoid broad abstraction layers that hide Linux kernel APIs without adding a
  real pci-sim concept.
* Treat sysfs files, module parameters, helper-script behavior, and
  guest-visible device behavior as user-visible interfaces.  Keep them stable
  unless changing them is intentional and documented.

Ownership, lifetime, and cleanup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* For every object, identify the owner and release path: host bridge, PCI
  resource, VF state, IOMMU object, VFIO device, TTY port, backing file,
  kthread, and allocated memory.
* Registration and allocation error paths must unwind in reverse order.
* Remove and module-exit paths must tolerate partially initialized state.
* Repeated load, test, failure, cleanup, and reload cycles should be reliable.
* Helper scripts should be idempotent and safe to run after partial failures.

Locking and concurrency
~~~~~~~~~~~~~~~~~~~~~~~

* Protect shared mutable state with the narrowest suitable kernel lock.
* Document lock ordering where more than one lock can be held.
* Review races between module unload, PF removal, VF enable/disable, VFIO MMIO
  access, TTY operations, kthreads, and cleanup scripts.
* Memory barriers and non-obvious ordering rules require comments explaining
  what they pair with and why they are needed.

PCI, SR-IOV, VFIO, and IOMMU expectations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Follow the kernel SR-IOV model around ``sriov_numvfs``: validate VF counts,
  reject invalid transitions, and cleanly remove VFs before disabling state.
* Keep VF personalities isolated so adding or changing UART behavior does not
  destabilize VFIO, IOMMU, or host-bridge behavior.
* Preserve VFIO isolation assumptions.  Review IOMMU group behavior, DMA
  mapping assumptions, BAR emulation, interrupt delivery, and reset semantics.
* Prefer debuggable correctness over clever emulation shortcuts.

Review checklist
----------------

Before considering a pci-sim change ready, verify:

* The change solves one logical problem.
* Formatting-only changes are separated from functional changes.
* The module builds and generated artifacts have been cleaned.
* ``checkpatch.pl`` has no new unhandled errors, warnings, or checks.
* Relevant build-warning gaps are reported.
* Runtime tests cover the paths affected by the change.
* Allocation, registration, error, remove, and unload paths are correct.
* Locking and object lifetimes are understandable from the code.
* New or changed module parameters, helper behavior, or user-visible behavior
  are documented.
