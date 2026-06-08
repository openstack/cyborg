=============================
Understanding Cyborg Policies
=============================

Cyborg's REST API policies use ``DocumentedRuleDefault`` with persona-based
defaults, completing the OpenStack TC's `Consistent and Secure RBAC community
goal`_. All policies use ``scope_types=['project']``, meaning only
project-scoped tokens are accepted.

.. _Consistent and Secure RBAC community goal:
   https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html

.. note::

   The ``scope_type`` of each policy is hardcoded to ``['project']`` and
   cannot be overridden via ``policy.yaml``.

Policy scope is always enforced for policies that define ``scope_types``.
System-scoped tokens are therefore rejected by Cyborg's project-scoped
policies. The :oslo.config:option:`oslo_policy.enforce_new_defaults` option
defaults to ``False`` in Cyborg during the 2026.2 transition window. When
``False``, oslo.policy accepts tokens that satisfy either the new
persona-based check string or the legacy deprecated bridge, so no endpoint
becomes more restrictive until the operator opts in.

Roles
-----

Cyborg uses the following Keystone roles. Keystone's implied-role
hierarchy means each role automatically includes the roles below it:
``admin`` → ``manager`` → ``member`` → ``reader``. The ``service``
role is separate and has no implication chain. Refer to the
`Keystone service API protection`_ documentation for the full
role hierarchy.

.. _Keystone service API protection:
   https://docs.openstack.org/keystone/latest/admin/service-api-protection.html

.. rubric:: ``reader``

Read-only access to resources within the caller's project. Cyborg uses the
``project_reader_or_admin`` base rule for ARQ read endpoints:

.. code-block:: python

   policy.RuleDefault(
       name='project_reader_api',
       check_str='role:reader and project_id:%(project_id)s',
   )

   policy.RuleDefault(
       name='project_reader_or_admin',
       check_str='rule:project_reader_api or rule:admin_api',
   )

A project reader can list and show ARQs belonging to their project.

.. rubric:: ``member``

Project-level write access. Nova currently uses the ``member`` role when
forwarding end-user tokens to Cyborg during instance scheduling. Cyborg
uses the ``project_member_or_service`` composite rule for ARQ write
endpoints:

.. code-block:: python

   policy.RuleDefault(
       name='project_member_api',
       check_str='role:member and project_id:%(project_id)s',
   )

   policy.RuleDefault(
       name='project_member_or_service',
       check_str='rule:project_member_api or rule:service_api',
   )

A project member can create, delete, and update ARQs.

.. rubric:: ``manager``

Project-level management access, above ``member`` but below cloud ``admin``.
Cyborg uses the ``project_manager_or_admin`` rule for hardware inventory
read endpoints:

.. code-block:: python

   policy.RuleDefault(
       name='project_manager_api',
       check_str='role:manager and project_id:%(project_id)s',
   )

   policy.RuleDefault(
       name='project_manager_or_admin',
       check_str='rule:project_manager_api or rule:admin_api',
   )

A project manager can read devices, deployables, and attributes for capacity
planning and troubleshooting. Hardware management operations (disable, enable,
program, attribute create/delete) remain restricted to cloud admins.

.. rubric:: ``service``

The ``service`` role is assigned to OpenStack service accounts for
machine-to-machine APIs. Cyborg's ARQ write endpoints accept the ``service``
role alongside ``member`` via the ``project_member_or_service`` rule,
preparing for Nova's future transition to presenting service credentials as
the primary token:

.. code-block:: python

   policy.RuleDefault(
       name='service_api',
       check_str='role:service',
   )

.. note::

   The ``service`` role must be assigned to Nova's service account in
   Keystone for service-token gating of bound ARQ operations to function.
   The ``manager`` and ``service`` roles are standard Keystone bootstrap
   roles available since the 2023.2 (Bobcat) release.

.. rubric:: ``admin``

Cloud administrator. Full access to all Cyborg APIs including all hardware
management operations:

.. code-block:: python

   policy.RuleDefault(
       name='admin_api',
       check_str='role:admin',
   )

Supported Role and Scope Combinations
--------------------------------------

Cyborg supports the following persona combinations. The ``scope_type`` is
always ``project`` and is not overridable.

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Persona
     - Role + Scope
     - Permitted operations
   * - ``ADMIN``
     - ``admin`` on project
     - All Cyborg APIs: hardware lifecycle management, device profiles,
       ARQ operations, hardware inventory reads and writes.
   * - ``PROJECT_MANAGER``
     - ``manager`` on project
     - Read hardware inventory: devices, deployables, attributes.
       Read device profiles and ARQs.
   * - ``PROJECT_MEMBER``
     - ``member`` on project
     - ARQ create, delete, update. Read device profiles and ARQs.
   * - ``PROJECT_READER``
     - ``reader`` on project
     - Read ARQs within own project. Read device profiles.
   * - ``SERVICE``
     - ``service`` on project
     - ARQ create, delete, update (machine-to-machine path).

Endpoint-Persona Mapping
-------------------------

The following table shows the policy rule and new default for every Cyborg
v2 API endpoint.

.. list-table::
   :header-rows: 1
   :widths: 42 35 23

   * - Endpoint
     - Policy rule
     - New default
   * - ``GET /v2/accelerator_requests``
     - ``cyborg:arq:get_all``
     - ``project_reader_or_admin``
   * - ``GET /v2/accelerator_requests/{arqs_uuid}``
     - ``cyborg:arq:get_one``
     - ``project_reader_or_admin``
   * - ``POST /v2/accelerator_requests``
     - ``cyborg:arq:create``
     - ``project_member_or_service``
   * - ``DELETE /v2/accelerator_requests``
     - ``cyborg:arq:delete``
     - ``project_member_or_service``
   * - ``PATCH /v2/accelerator_requests``
     - ``cyborg:arq:update``
     - ``project_member_or_service``
   * - ``GET /v2/device_profiles``
     - ``cyborg:device_profile:get_all``
     - ``project_reader_or_admin``
   * - ``GET /v2/device_profiles/{device_profiles_uuid}``
     - ``cyborg:device_profile:get_one``
     - ``project_reader_or_admin``
   * - ``POST /v2/device_profiles``
     - ``cyborg:device_profile:create``
     - ``admin_api``
   * - ``DELETE /v2/device_profiles/{device_profiles_uuid}``
     - ``cyborg:device_profile:delete``
     - ``admin_api``
   * - ``DELETE /v2/device_profiles?value={device_profile_name1}``
     - ``cyborg:device_profile:delete``
     - ``admin_api``
   * - ``GET /v2/devices``
     - ``cyborg:device:get_all``
     - ``project_manager_or_admin``
   * - ``GET /v2/devices/{uuid}``
     - ``cyborg:device:get_one``
     - ``project_manager_or_admin``
   * - ``POST /v2/devices/{uuid}/disable``
     - ``cyborg:device:disable``
     - ``admin_api``
   * - ``POST /v2/devices/{uuid}/enable``
     - ``cyborg:device:enable``
     - ``admin_api``
   * - ``GET /v2/deployables``
     - ``cyborg:deployable:get_all``
     - ``project_manager_or_admin``
   * - ``GET /v2/deployables/{uuid}``
     - ``cyborg:deployable:get_one``
     - ``project_manager_or_admin``
   * - ``PATCH /v2/deployables/{uuid}/program``
     - ``cyborg:deployable:program``
     - ``admin_api``
   * - ``GET /v2/attributes``
     - ``cyborg:attribute:get_all``
     - ``project_manager_or_admin``
   * - ``GET /v2/attributes/{uuid}``
     - ``cyborg:attribute:get_one``
     - ``project_manager_or_admin``
   * - ``POST /v2/attributes``
     - ``cyborg:attribute:create``
     - ``admin_api``
   * - ``DELETE /v2/attributes/{uuid}``
     - ``cyborg:attribute:delete``
     - ``admin_api``

Backward Compatibility
-----------------------

Backward compatibility is preserved through deprecated-rule bridges on every
migrated policy. When ``enforce_new_defaults = False`` (the Cyborg default in
2026.2), oslo.policy evaluates the new check string OR the legacy bridge, so
existing tokens that passed before continue to pass.

The deprecated bridge check strings are:

- ARQ reads: ``rule:admin_or_owner``
  (``is_admin:True or project_id:%(project_id)s``)
- ARQ create: ``rule:project_member_or_admin``
- ARQ writes: ``rule:admin_or_owner``
- Device, deployable, attribute endpoints: ``rule:admin_api``
- Device profile reads: legacy bridge ``rule:admin_or_owner``
  (new default ``project_reader_or_admin``)
- Device profile create/delete: legacy bridge ``rule:is_admin``
  (new default ``admin_api``)

.. note::

   System-scoped tokens are always rejected regardless of
   ``enforce_new_defaults``.

Migration Plan
--------------

**Step 1 — Ensure Keystone roles exist**

The ``manager`` and ``service`` roles are standard Keystone bootstrap roles
available since the 2023.2 (Bobcat) release. Re-running bootstrap on an
existing deployment is safe and idempotent.

**Step 2 — Assign the service role to Nova**

Nova's service account must have the ``service`` role for the hardcoded
service-token gate on bound ARQ operations to function. Assign it with::

   openstack role add --user <nova-service-user> \
       --project <service-project> service

**Step 3 — Opt in to new defaults (2026.2 and later)**

Set the following in ``cyborg.conf`` to enable new persona-based defaults::

   [oslo_policy]
   enforce_new_defaults = True

Before enabling, ensure all operators and service accounts have appropriate
role assignments. Project managers should have the ``manager`` role; Nova's
service account should have the ``service`` role.

**Step 4 — Verify**

Confirm that existing Nova-initiated instance scheduling still works (member
or service role ARQ operations) and that project managers can read hardware
inventory.

Transition Timeline
-------------------

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Release
     - Change
   * - **2026.2**
     - New persona-based defaults available.
       ``enforce_new_defaults`` defaults to ``False``.
       Operators may opt in early by setting
       ``enforce_new_defaults = True``.
   * - **2027.1**
     - ``enforce_new_defaults`` defaults to ``True``.
       Legacy deprecated bridges are formally deprecated with warnings.
       Operators not yet ready can set ``enforce_new_defaults = False``
       explicitly for one more cycle.
   * - **2027.2**
     - Deprecated legacy bridges removed.
       ``enforce_new_defaults = False`` will have no effect.
