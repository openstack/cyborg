========
Upgrades
========

This page summarizes how to upgrade Cyborg safely. Always read the
release-specific notes for your target version in addition to this guide.

API, conductor, and agents
--------------------------

For a predictable RPC and API surface, **run cyborg-api and
cyborg-conductor at the same release** during normal operation. A mixed
deployment (for example, mismatched API and conductor versions) is not a
supported operating mode: behavior and compatibility are not guaranteed across
that gap.

Typical component order when rolling out a new version is: **conductor**
and **API** first, then **agents**, so orchestration and the REST API match
before dataplane agents pick up changes. Adjust for your deployment tooling
if needed.

Database and online data migrations
-----------------------------------

Schema changes are applied with ``cyborg-dbsync upgrade``. Some releases
also ship **online data migrations** that backfill or fix data without
a new Alembic revision; those are run with:

.. code-block:: bash

    cyborg-dbsync online_data_migrations

A common pattern (see release notes for the exact sequence for each version)
is:

1. Install or update the ``cyborg-dbsync`` package (and shared libraries)
   so the tooling matches the target release.
2. Run ``cyborg-dbsync upgrade`` to apply pending schema migrations.
3. Run ``cyborg-dbsync online_data_migrations`` when release notes require
   it (for example, to backfill columns used for tenant isolation).
4. Upgrade Cyborg services, starting with conductor and API, then agents.

The cyborg-conductor service may also execute pending online data migrations
on startup as a safety net; running ``online_data_migrations`` explicitly
still ensures work completes before you rely on new enforcement.

Further references
------------------

* :doc:`/cli/cyborg-dbsync` — command-line reference for dbsync.
* :doc:`/cli/cyborg-status` — optional health and upgrade checks.
* :doc:`security` — service tokens, Keystone middleware, and ARQ access rules.
