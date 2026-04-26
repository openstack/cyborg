=============
cyborg-dbsync
=============

Synopsis
========

::

  cyborg-dbsync <command> [<args>]

Description
===========

:program:`cyborg-dbsync` is a tool for managing the Cyborg database schema
and performing data migrations.

Options
=======

The standard pattern for executing a :program:`cyborg-dbsync` command is::

    cyborg-dbsync <command> [<args>]

Run without arguments to see a list of available commands::

    cyborg-dbsync

Commands are:

* ``upgrade``
* ``revision``
* ``stamp``
* ``version``
* ``create_schema``
* ``online_data_migrations``

Detailed descriptions are below.

``cyborg-dbsync upgrade``
  Upgrade the database schema to the latest version. Optionally, use
  ``--revision`` to specify an alembic revision string to upgrade to.

``cyborg-dbsync revision``
  Create a new alembic revision. Use ``-m`` or ``--message`` to set the
  message string.

``cyborg-dbsync stamp``
  Stamp the database with a specific alembic revision.

``cyborg-dbsync version``
  Print the current database version information and exit.

``cyborg-dbsync create_schema``
  Create the database schema.

``cyborg-dbsync online_data_migrations``
  Perform online data migrations. Currently backfills the ``project_id``
  column on existing accelerator requests (ARQs) by querying Nova for
  the project that owns each bound instance.

  This command should be run after upgrading Cyborg to ensure that all
  ARQs have a correct ``project_id`` value. The cyborg-conductor service
  also runs this migration automatically on startup, but the CLI command
  allows operators to perform the migration at a convenient time and
  monitor progress.

  **Prerequisites**

  * Cyborg must be configured with a valid OpenStack SDK compute
    adapter (the ``[nova]`` group: auth URL, credentials, and region)
    so ``cyborg-dbsync`` can call the Nova API to resolve instance
    ownership. This is independent of ``[keystone_authtoken]``, which
    only applies to validating incoming API requests to Cyborg.
  * Nova must be running and accessible.

  **Return codes**

  The command prints the number of ARQs migrated and exits with code 0
  on success.
