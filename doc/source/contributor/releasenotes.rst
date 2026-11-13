.. _releasenotes:

Release Notes
=============

What is reno ?
--------------

Cyborg uses `reno <https://docs.openstack.org/reno/latest/>`__ for providing
release notes in-tree. A change that requires a release note must include it
with the implementation. Deferring the note to a follow-up change is
exceptional and must be explicitly agreed during review.

A multi-commit feature completed within one release may use one release note,
updated as the later commits merge. If development spans releases, each release
must have its own note describing the behavior and limitations delivered in
that release.

A *reno file* is a YAML file written in the ``releasenotes/notes`` tree which
is generated using the *reno* tool this way:

.. code-block:: bash

  $ tox -e venv -- reno new <name-your-file>

where usually ``<name-your-file>`` can be ``bp-<blueprint_name>`` for a
blueprint or ``bug-XXXXXX`` for a bugfix.

Refer to the `reno documentation
<https://docs.openstack.org/reno/latest/user/index.html>`__ for more
information.


When a release note is needed
-----------------------------

A release note is required anytime a reno section is needed. Below are some
examples for each section. Any sections that would be blank should be left out
of the note file entirely. If no section is needed, then you know you don't
need to provide a release note :-)

* ``upgrade``
    * A database change requires deployer action, such as running a migration
    * A configuration option is deprecated or removed, or its default changes
    * A change affects compatibility or the supported upgrade path
    * Any other change requires action from deployers

* ``security``
    * If the patch fixes a known vulnerability

* ``features``
    * A change adds or modifies user-visible API behavior
    * A user-facing command is added or changed, including new options for an
      existing command
    * A new accelerator driver is provided or an existing driver changes the
      :doc:`DriversSupportMatrix </admin/support-matrix>`

* ``critical``
    * Bugfixes categorized as Critical in launchpad *impacting users*

* ``fixes``
    * No clear definition of such bugfixes. Hairy long-standing bugs with high
      importance that have been fixed are good candidates though.

Cyborg does not use ``DocImpact``, ``APIImpact``, ``UpgradeImpact``, or other
``*Impact`` commit-message markers. Decide whether a note is required from the
actual user, operator, API, security, and upgrade effects of the change.

Use ``issues`` to document known user-visible limitations. The implementation
that introduces a limitation must include that information in its release note.
Release liaisons normally prepare ``prelude`` content near release time. Use
``other`` only when no more specific section fits.
