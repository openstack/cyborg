..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

================================
Quota Usage for Cyborg Resources
================================

Launchpad blueprint:
https://blueprints.launchpad.net/openstack-cyborg/+spec/cyborg-resource-quota

There are multiple ways to slice an OpenStack cloud. Imposing quota on these
various slices puts a limitation on the amount of resources that can be
consumed which helps to guarantee "fairness" or fair distribution of resources
at the creation time. If a particular project needs more resources, the
concept of quota gives the ability to increase the resource count on-demand,
given that the system constraints are not exceeded.


Problem description
===================
At present in Cyborg we don't have the concept of Quota on acceleration
resources, so users can consume as many resources as they want.
Quotas are tied closely to physical resources and billable entities, hence from
Cyborg's perspective, it helps to limit the allocation and consumption
of a particular kind of resources at a certain value.

In place of implementing quota like other services, we want to enable
the unified limit which is provided by Keystone to manage our quota limit[1].
With unified limits, all limits will be set in Keystone and enforced by
oslo.limit. So we decided to implement quota usage part first.
Once the oslo.limit is ready for other services, Cyborg will invoke oslo.limit
to get the limit information and do limit check etc.

This specs aims at the implementation of quota usage in Cyborg. As the
oslo.limit is not finished yet, we can directly set the value of limit
manually, and reserved the function calling oslo.limit with a "pass" inside.


Use cases
---------
Alice is an admin. She would like to have a feature which will give her
details of Cyborg acceleration resource consumptions so that she can manage her
resources appropriately.

She might run into following scenarios:

* Ability to know current resource consumption.

* Ability to prohibit overuse by a project.

* Prevent situation where users in a project get starved because users in
  other project consume all the resource. "Quota Management" would help to
  gurantee "fairness".

* Prevent DOS kind of attacks, abuse or error by users, which leads to an
  excessive amount of resources allocation.


Proposed change
===============
Proposed changes are introducing a Quota_Usage Table which primarily stores
the quota usage assigned for each resource in a project, and a Reservation
Table to store every modification of resource usage.

When a new resource allocation request comes, the 'reserved' field in the Quota
usages table will be updated. This acceleration resource is being used to set
up VM. For example, the fpga quota hardlimit is 5 and 3 fgpas have
already been used, then two new fpga requests come in. Since we have 3 fpgas
already used, the 'used' field will be set to 3. Now the 'reserved'
field will be set to 2 untill the fpga attachment is successful. Once
the attachment is done this field will be reset to 0, and the 'used'
count will be updated from 3 to 5. So at this moment, hardlimit is 5, used
is 5 and in-progress is 0. So there is one more request comes in, this request
will be rejected since there is not enough quota available.

In general,

Resource quota available = Resource hard_limit - [
(Resource reserved + Resources already allocated for project)]

In this specs, we just focus on the update of quota usage and we will not check
if one user has already exceed his quota limit. The limit management will be
set in Keystone in the future and we just need to invoke the oslo.limit.

Alternatives
------------
At present there is no quota infrastructure in Cyborg.

Adding Quota Management layer at the Orchestration layer could be an
alternative.However, our approach will give a finer view of resource
consumptions at the IaaS layer which can be used while provisioning Cyborg
resources.

Data model impact
-----------------
New Quota usages and reservation table will be introduced to Cyborg database to
store quota consumption for each resource in a project.

Quota usages table:

+---------------+--------------+------+-----+---------+----------------+
| Field         | Type         | Null | Key | Default | Extra          |
+---------------+--------------+------+-----+---------+----------------+
| created_at    | datetime     | YES  |     | NULL    |                |
| updated_at    | datetime     | YES  |     | NULL    |                |
| id            | int(11)      | NO   | PRI | NULL    | auto_increment |
| project_id    | varchar(255) | YES  | MUL | NULL    |                |
| resource      | varchar(255) | NO   |     | NULL    |                |
| reserved      | int(11)      | NO   |     | NULL    |                |
| used          | int(11)      | NO   |     | NULL    |                |
+---------------+--------------+------+-----+---------+----------------+

Quota reservation table:

+------------+--------------+------+-----+---------+----------------+
| Field      | Type         | Null | Key | Default | Extra          |
+------------+--------------+------+-----+---------+----------------+
| created_at | datetime     | YES  |     | NULL    |                |
| updated_at | datetime     | YES  |     | NULL    |                |
| deleted_at | datetime     | YES  |     | NULL    |                |
| deleted    | tinyint(1)   | YES  |     | NULL    |                |
| id         | int(11)      | NO   | PRI | NULL    | auto_increment |
| uuid       | varchar(36)  | NO   |     | NULL    |                |
| usage_id   | int(11)      | NO   | MUL | NULL    |                |
| project_id | varchar(255) | YES  | MUL | NULL    |                |
| resource   | varchar(255) | YES  |     | NULL    |                |
| delta      | int(11)      | NO   |     | NULL    |                |
| expire     | datetime     | YES  |     | NULL    |                |
+------------+--------------+------+-----+---------+----------------+

We will also introduce QuotaEngine class which represents the set of
recognized quotas and DbQuotaDriver class which performs check to enforcement
of quotas and also allows to obtain quota information.

REST API impact
---------------
Not sure if we need to expose GET quota usage before oslo.limit settle down.

Security impact
---------------
None

Notifications impact
--------------------
None

Other end user impact
---------------------
None

Performance Impact
------------------
None

Other deployer impact
---------------------
None

Developer impact
----------------
None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
Xinran WANG

Other contributors:
None

Work Items
----------

* Introduce Quota usages and Reservation table in Cyborg databases.
* Update these two tables during allocation and deallocation of resources.
* Reserve the place of function which will invoke oslo.limit with a "pass"
  inside.
* Add rollback mechanism when allocation fails.

Dependencies
============
None

Testing
=======

* Each commit will be accompanied with unit tests.
* Gate functional tests will also be covered.

Documentation Impact
====================
None

References
==========

[1] https://review.openstack.org/#/c/540803
