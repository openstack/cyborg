.. _maintainers-guide:

========================
Cyborg Maintainers Guide
========================

This guide explains what contributors and maintainers can expect during
review, how Cyborg delegates responsibility, and how to get a change reviewed.
It also describes the groups that administer Cyborg's bug trackers. It
complements the :doc:`/contributor/contributing` and
:doc:`/contributor/release-guide` guides.

OpenStack traditionally uses ``core reviewer`` or ``core team`` for people who
maintain a project. This guide uses ``maintainer`` more broadly. Everyone who
reviews changes, reports and triages bugs, improves documentation, or tests
releases helps maintain Cyborg. Gerrit group membership grants specific
permissions. You do not need those permissions to contribute to maintenance.

Governance and principles
=========================

Cyborg uses the OpenStack Project Team Lead (PTL) governance model. The current
PTL and project liaisons are listed on the `Cyborg governance page`_.

.. note::

   Cyborg may adopt the OpenStack distributed leadership model in the future.
   The delegation principles in this guide apply under either model. Under
   distributed leadership, the designated TaCT SIG liaison assumes the PTL's
   authority to add or remove maintainer group members.

.. _`Cyborg governance page`: https://governance.openstack.org/tc/reference/projects/cyborg.html

Cyborg follows the OpenStack community principles, including
`constructive peer review`_, and strives to `review the OpenStack way`_. All
changes are reviewed in Gerrit and tested by Zuul. Maintainers do not merge
directly to Git repositories; an approved change enters `project gating`_ and
merges only after its voting jobs pass.

.. _`constructive peer review`: https://governance.openstack.org/tc/reference/principles.html#we-value-constructive-peer-review
.. _`review the OpenStack way`: https://docs.openstack.org/project-team-guide/review-the-openstack-way.html
.. _`project gating`: https://zuul-ci.org/docs/zuul/latest/gating.html#project-gating

Beginning with the 2027.1 cycle, Cyborg uses a tiered maintainer model. The
model delegates authority by repository and responsibility so contributors can
take on larger roles without requiring membership in the project-wide core
team. It also creates a mentoring path and reduces reliance on any one
maintainer.

Gerrit maintainer groups
========================

The following sections describe the maintainer permissions. ``Code-Review +2``
means that a change is technically ready to merge, while ``Code-Review -2``
blocks it. ``Workflow +1``, also written ``+W``, approves the change for Zuul's
gate. ``Workflow -1``, also written ``-W``, means ``Work in progress``. Both
``-W`` and the default ``Workflow 0`` leave the change ineligible to merge, but
``-W`` is not used as a blocking review vote.

All contributors can participate in review. They may vote ``Code-Review +1``
to express support, vote ``Code-Review -1`` to identify a concern, or leave the
label at ``Code-Review 0`` when commenting without an overall vote. These
votes provide useful review input but do not approve or block the change. A
maintainer with ``Code-Review +2`` but without ``Workflow +1`` can provide a
complete technical review without approving the change for the gate.

Group inheritance is used where practical, but permissions must remain limited
to the repositories described below. Stable-branch permissions follow each
team's repository scope; membership in a repository-specific team must not
implicitly grant rights on unrelated Cyborg deliverables.

The `Cyborg Gerrit groups`_ page lists the current members of these teams.
Group membership, rather than this document, is the authoritative roster.

.. _`Cyborg Gerrit groups`: https://review.opendev.org/admin/groups/q/filter:cyborg

``cyborg-core``
---------------

``cyborg-core`` is the project-wide maintainer group. Its members have
``Code-Review -2..+2`` and ``Workflow -1..+1`` on maintained branches of all
official Cyborg deliverables:

* ``cyborg``
* ``python-cyborgclient``
* ``cyborg-specs``
* ``cyborg-tempest-plugin``

Core maintainers are expected to understand how changes across these
repositories affect Cyborg's design, compatibility, testing, releases, and
long-term maintenance. Core permissions may be granted directly or through
inclusion in the scoped groups below; in either case, ``cyborg-core`` retains
the project-wide rights described here.

Cyborg retains ``cyborg-core`` for maintainers with responsibility across the
project. The narrower groups let contributors take responsibility for selected
repositories without taking on that wider role. In particular,
``cyborg-approvers`` grants approval rights for the service, client, and specs,
but not the Tempest plugin.

``cyborg-approvers``
--------------------

``cyborg-approvers`` members have ``Code-Review -2..+2`` and
``Workflow -1..+1`` on:

* ``cyborg``
* ``python-cyborgclient``
* ``cyborg-specs``

Approvers may merge changes after considering the approval conventions in this
guide. The approver group is included in ``cyborg-reviewers`` and
``cyborg-stable``. Approvers should help mentor contributors and prospective
maintainers.

``cyborg-reviewers``
--------------------

``cyborg-reviewers`` members have ``Code-Review -2..+2`` on ``cyborg`` and
``python-cyborgclient``. This group does not grant ``Workflow +1`` on the
default branch. An approver must apply that vote before the change can enter
the gate.

This role recognizes contributors who can perform complete technical reviews
while they gain experience with approval decisions, release risk, and the
project's wider maintenance responsibilities.

``cyborg-stable``
-----------------

``cyborg-stable`` members have ``Code-Review -2..+2`` and
``Workflow -1..+1`` on the maintained stable branches of ``cyborg`` and
``python-cyborgclient``. Members of ``cyborg-reviewers`` and
``cyborg-approvers`` are included in this group. Before using stable-branch
permissions, they should understand the
`stable branch policy`_, `appropriate fixes`_, `stable review guidelines`_, and
`theory of upgrades`_.

.. _`stable branch policy`: https://docs.openstack.org/project-team-guide/stable-branches.html
.. _`appropriate fixes`: https://docs.openstack.org/project-team-guide/stable-branches.html#appropriate-fixes
.. _`stable review guidelines`: https://docs.openstack.org/project-team-guide/stable-branches.html#review-guidelines
.. _`theory of upgrades`: https://opendev.org/openstack/grenade/src/branch/master/README.rst#theory-of-upgrade

Stable permissions for other deliverables are granted through their
repository-specific maintainer groups. This prevents a role in one deliverable
from granting approval rights in another.

Tempest plugin groups
---------------------

The Tempest plugin is branchless and has no stable branches.
``cyborg-tempest-reviewers`` members have ``Code-Review -2..+2`` and
``cyborg-tempest-approvers`` members also have ``Workflow -1..+1``. The
approver group is included in the reviewer group. Both groups are scoped to
``cyborg-tempest-plugin`` only.

Members of the Tempest core team are included in both plugin groups. This lets
Tempest maintainers keep the plugin aligned with Tempest interfaces and
policies without granting them rights on unrelated Cyborg repositories.

Launchpad administration
========================

Launchpad administration, security liaison, and Gerrit maintainer roles may be
held by the same person. Under the PTL model, the PTL may perform these duties
directly while delegating them as trusted contributors are ready to assume the
responsibility. The groups below separate permissions so that delegation does
not require granting unrelated access.

OpenStack Administrators
------------------------

Cyborg's Launchpad projects and project groups must be owned by
`OpenStack Administrators`_. This ensures that project administration can be
recovered if Cyborg has no active member with the necessary rights.

.. _`OpenStack Administrators`: https://launchpad.net/~openstack-admins

``cyborg-bug-team``
-------------------

The `Cyborg bug team`_ is open to anyone and grants bug-triage permissions for
Cyborg's official Launchpad projects. Membership is automatically approved and
expires after one year.

.. _`Cyborg bug team`: https://launchpad.net/~cyborg-bug-team

The team triages bugs for:

* https://bugs.launchpad.net/openstack-cyborg
* https://bugs.launchpad.net/python-cyborgclient
* https://bugs.launchpad.net/cyborg-tempest-plugin

``cyborg-coresec``
------------------

The `Cyborg core security team`_ controls access to private security bugs. It
is a moderated, invitation-only group containing the PTL or security liaison
and, when needed, a small number of trusted approvers. Membership must be
reviewed at least once per cycle and inactive members must be removed or
deactivated.

.. _`Cyborg core security team`: https://launchpad.net/~cyborg-coresec

Access on the `Cyborg bug-sharing page`_ must be granted to teams rather than
individuals. It should be restricted to ``cyborg-coresec`` and the OpenStack
`Vulnerability Management team`_.

.. _`Cyborg bug-sharing page`: https://launchpad.net/openstack-cyborg/+sharing
.. _`Vulnerability Management team`: https://launchpad.net/~openstack-vuln-mgmt

``cyborg-drivers``
------------------

Cyborg approvers decide whether to accept a blueprint for a release. The
``cyborg-drivers`` team records that decision by approving and targeting the
blueprint to a series. It can also create series and administer the Launchpad
project. Because it can change bug-sharing permissions, membership should be
restricted to people who need those rights. The PTL may perform this work
directly. If a TaCT SIG liaison is appointed, they should be a member of
``cyborg-drivers``. Release liaisons may also be members when they need the
administrative rights for their role.

Membership expectations
=======================

Maintainer permissions reflect the team's trust in a contributor's judgment
and ongoing commitment to their part of Cyborg. Maintainers are expected to
review changes on most working days each week and a substantial proportion of
changes in their area over each release cycle. Regular review keeps
maintainers familiar with changes in their repositories. There is no required
pace for authoring patches. Review and maintenance are the main expectations.

These expectations are not numerical quotas. Participation can vary with
leave, personal commitments, time zones, other project responsibilities, and
the work available in a cycle. Core maintainers should maintain broad
engagement across Cyborg's deliverables; repository-scoped maintainers should
do so within their scope.

Maintainers should:

* provide technically sound reviews with actionable feedback;
* understand the repository's architecture and test strategy;
* consider compatibility, upgrades, stable branches, and release risk;
* help contributors make progress rather than only recording objections;
* participate in relevant Gerrit, IRC, mailing list, Launchpad, and planning
  discussions; and
* ask for specialist input when a change exceeds their expertise.

When you leave a negative vote, explain the concern and how the contributor
can address it. If a proposal is out of scope and revisions will not resolve
the concern, say so and explain why. That helps the contributor decide where
to put their effort.

Contributors do not need Gerrit permissions to be valued reviewers. Thoughtful
reviews and sustained work in a focused area are the normal path to a reviewer
role. Existing maintainers should mentor interested contributors, preferably in
public channels so others can learn from the discussion. Progression from
reviewer to approver or core is based on demonstrated judgment and broader
responsibility; it is not automatic or time based.

Adding and removing members
---------------------------

Under the PTL model, the PTL has final authority to add or remove members of
Cyborg's maintainer groups. The PTL should solicit input from existing
maintainers and discuss changes publicly when appropriate, but that
consultation does not transfer or limit the PTL's governance authority.

Membership should be reviewed regularly, normally at least once per release
cycle. Inactivity is not misconduct, and removal is not a judgment on the value
of past contributions. Keeping groups current protects the project and makes it
clear who has accepted an ongoing maintenance responsibility. A returning
contributor can be added again when they resume sustained participation.

Changes may be made at any time when a contributor is ready for additional
responsibility, a member asks to step down, permissions no longer match the
person's role, or project security requires prompt action.

Getting a change merged
=======================

A change must pass all voting Zuul jobs and receive:

* ``Code-Review +2`` from a maintainer with review rights for that repository
  and branch; and
* ``Workflow +1`` from a maintainer with approval rights for that repository
  and branch.

The same person may apply both votes and may approve a change they authored.
Independent review remains strongly preferred because it improves decisions,
shares knowledge, and develops future maintainers.

Approval conventions
--------------------

Cyborg is a small team, so waiting for a second approver on every change can
hold up useful work. We value consistent review and stable releases over a
rush to meet a milestone. Approvers should weigh each change's complexity and
potential impact when deciding how much independent review and waiting time
it needs.

An approver may merge a trivial change without waiting for another review.
For a non-trivial change without independent feedback, Cyborg uses lazy
consensus. An approver requests feedback and allows time for objections before
proceeding if none remain. This is especially important for changes authored
by the approver. The following steps are recommended:

#. request review explicitly in Gerrit and through an appropriate project
   channel, such as IRC, the weekly meeting, or the mailing list;
#. generally allow 3 to 30 days for contributors to respond. Choose a period
   based on complexity, impact, reversibility, test coverage, and proximity
   to a release milestone;
#. answer questions and resolve substantive objections; and
#. reconsider the waiting period after any substantial revision.

Silence is not a substitute for addressing a known concern. When risk or
consensus is unclear, seek another maintainer or subject-matter expert.
Waiting weeks or months to fix a bug, document a procedure, or accept a feature
does not serve users and raises the barrier to contribution.

Examples of changes that are usually trivial include:

* routine generated updates whose behavior and risk are well understood and
  whose CI jobs pass;
* translation updates, typo corrections, and small documentation fixes;
* additive unit, functional, or CI coverage that does not change production
  behavior; and
* other mechanical changes whose effect is obvious and readily reversible.

Patch size alone does not determine risk. A large mechanical update can be
trivial, while a one-line production change can alter compatibility or data
integrity. Changes involving APIs, databases, RPC interfaces, versioned
objects, security policy, upgrade behavior, or removal of test coverage are not
trivial. Disabling a CI job, skipping a test, or weakening coverage requires
particular care and should normally receive independent review.

Changes are easier to review when each commit has one coherent purpose. Split
large series at meaningful boundaries and keep every commit correct and
testable on its own. When a feature changes multiple layers, separate those
changes into commits in this order: versioned objects, database, RPC, and API.
Each successive layer generally carries a higher long-term maintenance and
upgrade compatibility cost.

Planning and tracking work
==========================

Launchpad is Cyborg's canonical bug and feature tracker. Bug fixes should have
a corresponding Launchpad bug. Use the standard ``Closes-Bug``,
``Partial-Bug``, or ``Related-Bug`` trailer described in
:doc:`/contributor/commit-messages`. An external issue may be linked from the
Launchpad bug, but third-party bug trackers must not be referenced directly in
commit messages or release notes.

Features should have a Launchpad blueprint. A small feature may instead be
tracked as a wishlist bug when the team agrees. API, database, and RPC changes
require a specification; most other non-trivial features should also have one.
The weekly team meeting is the normal place to resolve uncertainty about
whether a specification is required.

Blueprints and specifications are approved for one development cycle and must
be approved again if the work is not completed. Specifications should ideally
be proposed before milestone 1 and must be approved before the milestone 2 spec
freeze. Features should be complete by the milestone 3 feature freeze.

Cyborg follows the common OpenStack milestones and deadlines unless the team
agrees otherwise. The OpenStack Technical Committee and Release Management
team publish the `authoritative release schedule`_ and dates for each cycle.
See :doc:`/contributor/release-guide` for the actions and implications of each
milestone, including the exceptional feature freeze process and release
candidate policy.

.. _`authoritative release schedule`: https://releases.openstack.org/

Tests, documentation, and release notes
---------------------------------------

Code features must include unit tests. They should also include functional
coverage as Cyborg's functional suite matures. Tempest coverage is preferred
where practical. Hardware-dependent behavior may also need device emulation,
such as ``pci-sim``, when third-party CI cannot validate the integration.

Gating CI requires the tests to pass for every commit. For a bug fix,
contributors are encouraged to use a two-commit regression-test series:

#. The first commit adds a passing reproducer test that exercises and asserts
   the existing broken behavior.
#. The second commit depends on the reproducer, updates the test to assert the
   correct behavior, and fixes the production code.

These are two separate commits, normally proposed as two dependent Gerrit
changes, and both remain in the final Git history. They are not two patch sets
of one Gerrit change. A new patch set replaces an earlier revision of the same
commit; it does not add another commit to the final history.

For example, the merged history should retain both commits::

    Fix device allocation after an interrupted request
    Add a reproducer for interrupted device allocation

The reproducer commit passes by documenting the faulty result. The dependent
fix commit changes that expectation to the intended result while correcting the
implementation. This keeps every commit independently testable.

Tests, documentation, and applicable release notes must be developed alongside
the implementation. Include them in the commits that introduce or change the
behavior rather than deferring them until after the work is complete.

For a bug fix or simple feature, the commit that completes the work normally
includes the release note and relevant user, operator, API, and developer
documentation. Minor editorial refinements may follow, but the change should be
adequately tested and documented when it merges.

A larger feature may deliver useful behavior incrementally. For example, an
initial usable implementation may have three documented limitations, with
three subsequent commits removing them. Each commit should update the tests and
documentation to describe the behavior and remaining limitations at that point.
If all four commits merge in the same release, one release note may describe
the combined result and be updated as the later commits merge. This does not
require a separate release note for every commit.

When a feature spans releases, each release must have its own release note that
describes the behavior and limitations delivered in that release. Documentation
must likewise describe the behavior that users and operators receive rather
than only the intended final design.

See :doc:`/contributor/releasenotes` for release-note guidance and
:doc:`/contributor/microversions` for API microversion requirements.

When requirements are unclear, ask a maintainer in Gerrit, IRC, or on the
mailing list before investing heavily in an implementation.

Getting review attention
========================

.. _gerrit-change-conventions:

Gerrit change conventions
-------------------------

Cyborg uses two visible conventions for work in progress: apply
``Workflow -1`` (``-W``), or prefix the commit subject with ``[WIP]``. The
``-W`` vote makes the change ineligible to merge. ``[WIP]`` communicates the
same intent to reviewers
but does not mechanically prevent approval. Remove the marker when the change
is ready.

Do not use Gerrit's native work-in-progress or draft features because they
reduce change visibility and make reviewer feedback harder to obtain.

Prefix a change with ``[DNM]`` (Do Not Merge) when it is not intended to merge,
such as an experiment used to test a CI job. This is a human-facing convention
and does not mechanically block submission; the change should remain
unapproved.

Use Gerrit topics, not hashtags, to group related changes. Topic names must not
contain spaces and use these forms:

* Bugs use ``bug/<launchpad-number>``, for example ``bug/1234567``.
* Blueprint features use ``bp/<blueprint-slug>``. Use the exact slug from
  Launchpad.
* Wishlist features tracked as bugs use ``bug/<launchpad-number>`` because they
  do not have a blueprint slug.

Topics supplement rather than replace commit-message trailers such as
``Closes-Bug`` or ``Implements``.

A change proposed directly to a stable branch without first being proposed to
the default branch is exceptional and should use ``[stable-only]`` at the start
of the commit subject. This is rarely appropriate outside CI or other genuinely
branch-specific changes. The commit message should explain why the change does
not apply to the default branch. Normal backports should retain the
``cherry-pick -x`` provenance line instead of using ``[stable-only]``.

Preparing a change for review
-----------------------------

Before requesting review, check that the change:

* has the required bug, blueprint, or specification;
* targets the newest applicable branch;
* passes its relevant tests and CI jobs; and
* includes the tests, documentation, and release note required by its scope.

Features target the default branch. A bug that affects the default branch
should normally be fixed there first and then backported from newer to older
maintained branches. If a bug affects only a stable release, propose the fix to
the newest affected stable branch first.

Requesting review
-----------------

If a new contributor has not received maintainer feedback within 1--3 working
days, they may add relevant maintainers as Gerrit reviewers or ask in
``#openstack-cyborg``. If the change remains unattended for about a week, add
it to the review section of the weekly meeting agenda or start a mailing-list
thread that introduces the problem and links to the review.

The team aims to provide initial feedback within two weeks. Release
milestones, PTGs, leave, security work, and other demands can make that
impossible. A polite reminder is welcome; an overlooked change is more likely
than intentional silence.

After review begins, respond to questions and requested changes promptly when
possible. Contributors and maintainers work across many time zones and should
not work outside their normal hours. A response within a day or two is usually
prompt. Longer gaps are understandable, but the reviewer may need additional
time to restore context.

AI-assisted development and linting
===================================

Cyborg welcomes tools that help contributors produce higher-quality changes,
but contributors remain responsible for understanding and explaining
everything they submit. Repeated mistakes may justify a lint rule or tool
update, preferably as a separate change.

AI assistance does not replace human judgment or the review process described
in this guide. Follow :doc:`/contributor/agentic-coding` for repository
guidance and :doc:`/contributor/commit-messages` for required AI attribution.
