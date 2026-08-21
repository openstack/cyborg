.. _repo-overview:

=============
Repo Overview
=============

A terse map of the Cyborg repository for contributor orientation.

Root Files
==========

``HACKING.rst``
    Cyborg coding style rules.
``AGENTS.md``
    Agent routing index and policy.
``.tmp/``
    Gitignored local scratch directory for notes, plans, and ephemeral output.
``tox.ini``
    Test environments, commands, and environment variables.
``pyproject.toml``
    Build system (pbr), project metadata, entry points, and dependencies.
``requirements.txt`` / ``test-requirements.txt``
    Runtime and test dependencies (pinned via OpenStack constraints).

cyborg/ Package
===============

``cyborg/api/``
    REST API layer: WSGI, routing, controllers, policy enforcement.
``cyborg/agent/``
    Agent manager: runs on compute hosts, discovers and manages accelerators.
``cyborg/conductor/``
    Conductor manager: orchestrates placement updates and device bindings.
``cyborg/accelerator/``
    Accelerator drivers for FPGA, GPU, NIC, SSD, and other device types.
``cyborg/accelerator/drivers/``
    Per-vendor driver implementations (Intel, Nvidia, Huawei, Xilinx, Inspur).
``cyborg/db/``
    Database API abstraction layer (SQLAlchemy models and migrations).
``cyborg/objects/``
    Versioned objects: the canonical data model for RPC payloads.
``cyborg/image/``
    Glance integration: image metadata for accelerator programming.
``cyborg/cmd/``
    Entry points for Cyborg services (``cyborg-api``, ``cyborg-agent``,
    ``cyborg-conductor``, ``cyborg-dbsync``, ``cyborg-status``).
``cyborg/conf/``
    oslo.config option declarations, one file per subsystem.
``cyborg/policies/``
    oslo.policy rule definitions for API access control.
``cyborg/common/``
    Shared utilities, constants, and configuration loading.
``cyborg/tests/``
    Unit (``unit/``) and functional (``functional/``) test suites.

doc/ Structure
==============

``doc/source/admin/``
    Operator guides: deployment, configuration, driver support matrix.
``doc/source/contributor/``
    Developer guides: process, testing, driver development, agentic coding.
    Also contains REST API microversion history
    (``rest_api_version_history.rst``) and release notes documentation
    (``releasenotes.rst``).
``doc/source/user/``
    End-user guides: using Cyborg with device profiles and ARQs.
``doc/source/cli/``
    cyborg-status CLI reference.
``doc/source/configuration/``
    Configuration guide and per-driver setup documentation.

releasenotes/
=============

Repository root directory containing Reno release notes (``notes/`` source
files + ``source/`` for rendered output).

API Docs
========

These live at the repository root, separate from ``doc/``.

``api-ref/``
    REST API reference: per-resource ``.inc`` files and an index. Built and
    published to docs.openstack.org.
