..
      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

Chronological Release Liaison Guide
====================================

This is a reference guide that a release liaison may use as an aid, if
they choose.

Cyborg uses the standard `Project Team Lead (PTL)`__ governance model.
The release liaison is appointed by the PTL and is responsible for
requesting releases, reviewing Feature Freeze Exception (FFE) requests,
and coordinating release-related activities with the team.

.. __: https://governance.openstack.org/tc/reference/project-team-lead.html

How to Use This Guide
---------------------

This guide is organized chronologically to follow the OpenStack release
cycle from PTG planning through post-release activities. You can use it
in two ways:

**For New Release Liaisons**
    Read through the entire guide to understand the full release cycle,
    then bookmark it for reference during your term.

**For Experienced Release Liaisons**
    Jump directly to the relevant section for your current phase in the
    release cycle. Each major section corresponds to a specific time period.

**Key Navigation Tips**
    * The :ref:`glossary` defines all acronyms and terminology used
    * Time-sensitive activities are clearly marked by milestone phases
    * PTL coordination notes indicate when team collaboration is required

**Placeholder Convention**
    Terms shown in ``<angle-brackets>`` (e.g., ``<release>``,
    ``<stable branch>``) are placeholders that must be replaced with
    the actual values for your cycle.

PTL Coordination
-----------------

The release liaison works under the PTL to manage release activities.
The release liaison has authority for release-specific decisions (FFE
approvals, release timing, etc.) while major process changes and strategic
decisions are made by the PTL with team input.

This coordination approach ensures that:

* Release activities are properly managed by a dedicated liaison
* The PTL is kept informed of release progress and issues
* Team input is gathered for significant decisions
* Release processes remain responsive while maintaining team alignment

Project Context
---------------

* Coordinate with the cyborg meeting (chair rotates each meeting, with
  volunteers requested at the end of each meeting)

  * Meeting etherpad: https://etherpad.opendev.org/p/openstack-cyborg-irc-meeting
  * IRC channel: #openstack-cyborg

* Get acquainted with the release schedule

  * Example: https://releases.openstack.org/<current-release>/schedule.html

* Familiarize yourself with Cyborg project repositories and tracking:

Cyborg Main Repository
    `Primary codebase for the Cyborg service <https://opendev.org/openstack/cyborg>`__

Cyborg Specifications
    `Design specifications <https://opendev.org/openstack/cyborg-specs>`__ (not released)

Python Cyborg Client
    `Command-line client and Python library <https://opendev.org/openstack/python-cyborgclient>`__

Cyborg Tempest Plugin
    `Integration tests <https://opendev.org/openstack/cyborg-tempest-plugin>`__ (follows tempest cycle)

Cyborg Launchpad (Main)
    `Primary bug and feature tracking <https://launchpad.net/cyborg>`__

Python Cyborg Client Launchpad
    `Client library tracking <https://launchpad.net/python-cyborgclient>`__

Cyborg Tempest Plugin Launchpad
    `Test plugin tracking <https://launchpad.net/cyborg-tempest-plugin>`__

Project Team Gathering
----------------------

Event Liaison Coordination
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Work with the project team to select an event liaison for PTG coordination.
  The event liaison is responsible for:

  * Reserving sufficient space at PTG for the project team's meetings
  * Putting out an agenda for team meetings
  * Ensuring meetings are organized and facilitated
  * Documenting meeting results

* If no event liaison is selected, these duties revert to the release liaison.

* Monitor for OpenStack Events team queries on the mailing list requesting
  event liaison volunteers - teams not responding may lose event
  representation.

PTG Planning and Execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Create PTG planning etherpad, retrospective etherpad and alert about it in
  cyborg meeting and dev mailing list

  * Example: https://etherpad.opendev.org/p/cyborg-2026.2-ptg

* Run sessions at the PTG (if no event liaison is selected)

* Do a retro of the previous cycle

* Coordinate with team to establish agreement on the agenda for this release:

  * **Review Days Planning**: determine number of review days allocated
    for specs and implementation work
  * **Freeze Dates Coordination**: define Spec approval and Feature
    freeze dates through team collaboration
  * **Release Schedule Modifications**: modify the OpenStack release
    schedule if needed by proposing new dates
    (Example: https://review.opendev.org/c/openstack/releases/+/877094)

* Discuss the implications of the `SLURP or non-SLURP`__ current release

.. __: https://governance.openstack.org/tc/resolutions/20220210-release-cadence-adjustment.html

* Sign up for group photo at the PTG (if applicable)


After PTG
---------

* Send PTG session summaries to the dev mailing list

* Add `RFE bugs`__ if you have action items that are simple to do but
  without an owner yet.

* Update IRC #openstack-cyborg channel topic to point to new
  development-planning etherpad.

.. __: https://bugs.launchpad.net/cyborg/+bugs?field.tag=rfe

A few weeks before milestone 1
------------------------------

* Plan a spec review day

* Periodically check the series goals others have proposed in the “Set series
  goals” link:

  * Example: https://blueprints.launchpad.net/cyborg/<current-release>/+setgoals

Milestone 1
-----------

* Release cyborg and python-cyborgclient via the openstack/releases repo.
  Cyborg follows the `cycle-with-intermediary`__ release model:

.. __: https://releases.openstack.org/reference/release_models.html#cycle-with-intermediary

  * Create actual releases (not just launchpad bookkeeping) at milestone points
  * No launchpad milestone releases are created for intermediary releases
  * When releasing the first version of a library for the cycle, bump
    the minor version to leave room for future stable branch releases

* Release stable branches of cyborg

Stable Branch Release Process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prepare the stable branch for evaluation:

.. code-block:: bash

   git checkout <stable branch>
   git log --no-merges <last tag>..

Analyze commits to determine version bump according to semantic versioning.

Semantic Versioning Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose version bump based on changes since last release:

Major Version (X)
    Backward-incompatible changes that break existing APIs

Minor Version (Y)
    New features that maintain backward compatibility

Patch Version (Z)
    Bug fixes that maintain backward compatibility

Release Command Usage
~~~~~~~~~~~~~~~~~~~~~

Generate the release using OpenStack tooling:

* Use the `new-release command
  <https://releases.openstack.org/reference/using.html#using-new-release-command>`__
* Propose the release with version according to chosen semver format
  (x.y.z)

Summit
------

**Responsibility Precedence for Summit Activities:**

1. **Project Update/Onboarding Liaisons** (if appointed):

   * **Project Update Liaison**: responsible for giving the project update
     showcasing team's achievements for the cycle to the community
   * **Project Onboarding Liaison**: responsible for giving/facilitating
     onboarding sessions during events for the project's community

2. **Event Liaison** (if no Project Update/Onboarding liaisons exist):

   * Coordinates all Summit activities including project updates and onboarding

3. **Release Liaison** (if no Event Liaison is appointed):

   * Work with the team to ensure Summit activities are properly handled:

     * Prepare the project update presentation
     * Prepare the on-boarding session materials
     * Prepare the operator meet-and-greet session

.. note::

   The team can choose to not have a Summit presence if desired.

A few weeks before milestone 2
------------------------------

* Plan a spec review day (optional)

Milestone 2
-----------

* Spec freeze (unless changed by team agreement at PTG)

* Release cyborg and python-cyborgclient (if needed)

* Stable branch releases of cyborg


Shortly after spec freeze
-------------------------

* Create a blueprint status etherpad to help track, especially non-priority
  blueprint work, to help things get done by Feature Freeze (FF). Example:

  * https://etherpad.opendev.org/p/cyborg-<release>-blueprint-status

* Create or review a patch to add the next release’s specs directory so people
  can propose specs for next release after spec freeze for current release

Milestone 3
-----------

* Feature freeze day

* Client library freeze, release python-cyborgclient

* Close out all blueprints, including “catch all” blueprints like mox,
  versioned notifications

* Stable branch releases of cyborg

* Start writing the `cycle highlights
  <https://docs.openstack.org/project-team-guide/release-management.html#cycle-highlights>`__

Week following milestone 3
--------------------------

* If warranted, announce the FFE (feature freeze exception process) to
  have people propose FFE requests to a special etherpad where they will
  be reviewed.
  FFE requests should first be discussed in the IRC meeting with the
  requester present.
  The release liaison has final decision on granting exceptions.

  .. note::

    if there is only a short time between FF and RC1 (lately it’s been 2
    weeks), then the only likely candidates will be low-risk things that are
    almost done. In general Feature Freeze exceptions should not be granted,
    instead features should be deferred and reproposed for the next
    development cycle. FFE never extend beyond RC1.

* Mark the max microversion for the release in the
  :doc:`/contributor/rest_api_version_history`

A few weeks before RC
---------------------

* Update the release status etherpad with RC1 todos and keep track
  of them in meetings

* Go through the bug list and identify any rc-potential bugs and tag them

RC
--

* Follow the standard OpenStack release checklist process

* If we want to drop backward-compat RPC code, we have to do a major RPC
  version bump and coordinate it just before the major release:

  * https://wiki.openstack.org/wiki/RpcMajorVersionUpdates

  * Example: https://review.opendev.org/541035

* “Merge latest translations" means translation patches

  * Check for translations with:

    * https://review.opendev.org/#/q/status:open+project:openstack/cyborg+branch:master+topic:zanata/translations

* Should NOT plan to have more than one RC if possible. RC2 should only happen
  if there was a mistake and something was missed for RC, or a new regression
  was discovered

* Write the reno prelude for the release GA

  * Example: https://review.opendev.org/644412

* Push the cycle-highlights in marketing-friendly sentences and propose to the
  openstack/releases repo. Usually based on reno prelude but made more readable
  and friendly

  * Example: https://review.opendev.org/644697

Immediately after RC
--------------------

* Look for bot proposed changes to reno and stable/<cycle>

* Create the launchpad series for the next cycle

* Set the development focus of the project to the new cycle series

* Set the status of the new series to “active development”

* Set the last series status to “current stable branch release”

* Set the previous to last series status to “supported”

* Repeat launchpad steps ^ for all cyborg deliverables.

* Make sure the specs directory for the next cycle gets created so people can
  start proposing new specs

* Make sure to move implemented specs from the previous release

  * Move implemented specs manually (TODO: add tox command in future)

  * Remove template files:

    .. note::

       The specs directory lives in the
       `cyborg-specs <https://opendev.org/openstack/cyborg-specs>`__
       repository. Run these commands there, not in the main cyborg
       repo.

    .. code-block:: bash

       rm doc/source/specs/<release>/index.rst
       rm doc/source/specs/<release>/template.rst

* Ensure liaison handoff: either transition to new release liaison or confirm
  reappointment for next cycle

.. _glossary:

Glossary
--------

PTL
    Project Team Lead - The elected leader of an OpenStack project team,
    responsible for overall project governance and coordination.

FFE
    Feature Freeze Exception - A request to add a feature after the feature
    freeze deadline. Should be used sparingly for low-risk, nearly
    complete features.

GA
    General Availability - The final release of a software version for
    production use.

PTG
    Project Team Gathering - A collaborative event where OpenStack project
    teams meet to plan and coordinate development activities.

RC
    Release Candidate - A pre-release version that is potentially the final
    version, pending testing and bug fixes.

RFE
    Request for Enhancement - A type of bug report requesting a new feature
    or enhancement to existing functionality.

SLURP
    Skip Level Upgrade Release Process - An extended maintenance release
    that allows skipping intermediate versions during upgrades.

Summit
    OpenStack Summit - A conference where the OpenStack community gathers
    for presentations, discussions, and project updates.

Miscellaneous Notes
-------------------

How to track launchpad blueprint approvals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Core team approves blueprints through team consensus. The release liaison
ensures launchpad status is updated correctly after core team approval:

* Set the approver as the core team member who approved the spec

* Set the Direction => Approved and Definition => Approved and make sure the
  Series goal is set to the current release. If code is already proposed, set
  Implementation => Needs Code Review

* Optional: add a comment to the Whiteboard explaining the approval,
  with a date
  (launchpad does not record approval dates). For example: “We discussed this
  in the team meeting and agreed to approve this for <release>. -- <nick>
  <YYYYMMDD>”

How to complete a launchpad blueprint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Set Implementation => Implemented. The completion date will be recorded by
  launchpad
