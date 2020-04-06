============================
So You Want to Contribute...
============================

For general information on contributing to OpenStack, please check out the
`contributor guide <https://docs.openstack.org/contributors/>`_ to get started.
It covers all the basics that are common to all OpenStack projects: the
accounts you need, the basics of interacting with our Gerrit review system,
how we communicate as a community, etc.

Below will cover the more project specific information you need to get started
with {{cookiecutter.service}}.

Communication
~~~~~~~~~~~~~

We use the #openstack-cyborg IRC channel.

The weekly meetings happen in this channel. You can find the meeting times,
previous meeting logs and proposed meeting agendas at
`Cyborg Team Meeting Page
<https://wiki.openstack.org/wiki/Meetings/CyborgTeamMeeting>`_.

Contacting the Core Team
~~~~~~~~~~~~~~~~~~~~~~~~

The core reviewers of Cyborg and their emails are listed in
`Cyborg core team <https://review.opendev.org/#/admin/groups/1243,members>`_.

New Feature Planning
~~~~~~~~~~~~~~~~~~~~

To propose or plan new features, we add a new story in the
`Cyborg Storyboard
<https://storyboard.openstack.org/#!/project/openstack/cyborg>`_
and/or propose a specification in the
`cyborg-specs <https://opendev.org/openstack/cyborg-specs>`_ repository.

Task Tracking
~~~~~~~~~~~~~

We track our tasks in the `Cyborg Storyboard
<https://storyboard.openstack.org/#!/project/openstack/cyborg>`_.

If you're looking for some smaller, easier work item to pick up and get started
on, ask in the IRC meeting.

Reporting a Bug
~~~~~~~~~~~~~~~

You found an issue and want to make sure we are aware of it? You can do so
by adding an entry in the `Cyborg Storyboard
<https://storyboard.openstack.org/#!/project/openstack/cyborg>`_ or raising
it in the IRC meeting.

Getting Your Patch Merged
~~~~~~~~~~~~~~~~~~~~~~~~~

To merge a patch, it must pass all voting Zuul checks and get two +2s from
core reviewers. We strive to avoid scenarios where one person from a company
or organization proposes a patch, and two other core reviewers from the
same organization approve it to get it merged. In other words, at least
one among the patch author and the two approving reviwers must be from
another organization.

We are constantly striving to improve quality. Proposed patches must
generally have unit tests and/or functional tests that cover the changes,
and strive to improve code coverage.

Project Team Lead Duties
~~~~~~~~~~~~~~~~~~~~~~~~

All common PTL duties are enumerated in the `PTL guide
<https://docs.openstack.org/project-team-guide/ptl.html>`_.
