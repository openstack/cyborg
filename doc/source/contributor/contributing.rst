============================
So You Want to Contribute...
============================

For general information on contributing to OpenStack, please check out the
`contributor guide <https://docs.openstack.org/contributors/>`_ to get started.
It covers all the basics that are common to all OpenStack projects: the
accounts you need, the basics of interacting with our Gerrit review system,
how we communicate as a community, etc.

Below will cover the more project specific information you need to get started
with Cyborg.

Communication
~~~~~~~~~~~~~

We use the #openstack-cyborg channel on the `OFTC <http://oftc.net>`_ IRC network.

The weekly meetings happen in this channel. You can find the meeting times,
previous meeting logs and proposed meeting agendas at
`Cyborg Team Meeting Page
<https://etherpad.opendev.org/p/openstack-cyborg-irc-meeting>`_.

The openstack-discuss mailing list is another way we make announcement and
discuss some topics in public. Cyborg related discussions usually start with
tag:[cyborg].
`<The openstack-discuss Archives http://lists.openstack.org/pipermail/openstack-discuss/>`_

Contacting the Maintainers
~~~~~~~~~~~~~~~~~~~~~~~~~~

Beginning with the 2027.1 cycle, Cyborg uses a tiered maintainer model that
delegates review and approval rights by repository and responsibility. The
model gives contributors a path to take on wider responsibilities without
requiring immediate membership in the project-wide core team.

Contact maintainers through Gerrit, the ``#openstack-cyborg`` IRC channel,
or the openstack-discuss mailing list. If the first person you contact cannot
help, they can direct you to an appropriate maintainer or subject-matter
expert. See
:doc:`/contributor/maintainers-guide` for the team structure, membership
expectations, review policy, and advice on getting a change reviewed.

New Feature Planning
~~~~~~~~~~~~~~~~~~~~

Track a proposed feature with a `Cyborg Launchpad blueprint
<https://blueprints.launchpad.net/openstack-cyborg>`_. With team agreement, a
small feature may instead use a wishlist bug. API, database, and RPC changes
require a specification in the
`cyborg-specs <https://opendev.org/openstack/cyborg-specs>`_ repository. Most
other non-trivial features should also have one. See
:doc:`/contributor/maintainers-guide` for planning and approval guidance.

Task Tracking
~~~~~~~~~~~~~

We track our tasks in the `Launchpad <https://bugs.launchpad.net/openstack-cyborg>`_.

Planned goals follow the `OpenStack release schedule
<https://releases.openstack.org/>`_ and are tracked as `Cyborg blueprints
<https://blueprints.launchpad.net/openstack-cyborg>`_. If you are looking for
a smaller introductory task, ask in the IRC meeting.

Reporting a Bug
~~~~~~~~~~~~~~~

You found an issue and want to make sure we are aware of it? You can do so on
`Launchpad <https://bugs.launchpad.net/openstack-cyborg/+filebug>`__.
More info about Launchpad usage can be found on `OpenStack docs page
<https://docs.openstack.org/contributors/common/task-tracking.html#launchpad>`_.
But before you report a bug or register a new feature, we recommend you to
check if it is already registered there. Otherwise, it might be a duplicated
patch and will be abandoned. If you're still confused, as a more efficient
way, we encourage you to go and ask PTL and cores in the IRC channel directly.
Or mail PTL if IRC is not convenient for you.

Getting Your Patch Merged
~~~~~~~~~~~~~~~~~~~~~~~~~

Changes must pass the required Zuul checks and receive ``Code-Review +2``
and ``Workflow +1`` from maintainers authorized for the repository and branch.
Independent review is encouraged; one authorized approver may provide both
votes.

See :doc:`/contributor/maintainers-guide` for approval conventions, guidance
on preparing changes, and help getting review attention.

Project Team Lead Duties
~~~~~~~~~~~~~~~~~~~~~~~~

All common PTL duties are enumerated in the `PTL guide
<https://docs.openstack.org/project-team-guide/ptl.html>`_.

API Policy Targets
~~~~~~~~~~~~~~~~~~

Cyborg API controllers use the request context as the policy target. The
``@authorize_wsgi.authorize_wsgi`` decorator must be the outermost (first)
decorator on an API method. Policy checks receive a target containing the
caller's ``project_id`` and ``user_id``::

  {
      'project_id': context.project_id,
      'user_id': context.user_id,
  }

This is important for project-scoped persona rules such as
``project_id:%(project_id)s``. Passing an empty target would make those
checks fail for non-admin project users.

Global resources, such as device profiles, should use admin-only policy
rules rather than relying on an empty target. If an API needs policy to
enforce ownership of an existing resource, fetch the resource first and
pass a target built from the resource's project or user fields.

ARQ ownership is enforced below the API policy check. ``ExtARQ.get()``,
``ExtARQ.list()``, and ``ExtARQ.destroy()`` pass a project filter to the
DB layer for non-admin contexts, and the DB methods apply that
``project_id`` filter before returning, updating, or deleting rows.
