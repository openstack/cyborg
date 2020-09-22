=============================
Understanding Cyborg Policies
=============================

.. warning::

   JSON formatted policy file is deprecated since Cyborg (Victoria).
   Use YAML formatted file. Use `oslopolicy-convert-json-to-yaml`__ tool
   to convert the existing JSON to YAML formatted policy file in backward
   compatible way.

.. __: https://docs.openstack.org/oslo.policy/latest/cli/oslopolicy-convert-json-to-yaml.html

Cyborg supports a rich policy system that has evolved significantly over its
lifetime. Initially, cyborg policy defaults have been defined in the codebase,
requiring the ``policy.json`` file only to override these defaults. Starting in
the Victoria release, policy file has been changed from ``policy.json``
to ``policy.yaml``.

The old default policy in Cyborg is incomplete and not good enough. Since
Cyborg V2 API is newly implemented in Train, RBAC check for V2 API still
remains incomplete. So in the Ussuri release, the specification of policy
refresh was approved. In the Victoria release, Cyborg landed the new default
roles to improve some issues that had been identified:

#. No ``allow``. Old policy ``allow`` means any access will be passed.
   ``allow`` rule was used by cyborg:arq:create, which is too slack.

#. No global vs project admin. The old role ``is_admin`` is used for the global
   admin that is able to make almost any change to Cyborg, and see all details
   of the Cyborg system. The rule passes for any user with an admin role, it
   doesn’t matter which project is used.

#. No ``admin_or_owner``. Old role ``admin_or_owner`` sounds like it checks if
   the user is a member of a project. However, for most APIs we use the default
   target which means this rule will pass for any authenticated user.

#. Introduce ``scope_type`` and ``reader`` role. There still some cases which
   are not well covered. For example, it is impossible to allow a user to
   retrieve/update devices which are shared by multiple projects from a system
   level without being given the global admin role. In addition, cyborg now
   doesn’t have a ``reader`` role.

Keystone comes with ``admin``, ``member`` and ``reader`` roles by default.
Please refer to `keystone document <https://docs.openstack.org/keystone/latest//admin/service-api-protection.html>`__
for more information about these new defaults. In addition, keystone supports
a new "system scope" concept that makes it easier to protect deployment level
resources from project or system level resources. Please refer to
`token scopes <https://docs.openstack.org/keystone/latest//admin/tokens-overview.html#authorization-scopes>`__
and `system scope specification <https://specs.openstack.org/openstack/keystone-specs/specs/keystone/queens/system-scope.html>`__
to understand the scope concept.

In the Cyborg (Victoria) release, Cyborg policies implemented
the scope concept and default roles provided by keystone (admin, member,
and reader). Using common roles from keystone reduces the likelihood of
similar, but different, roles implemented across projects or deployments.
With the help of the new defaults it is easier to understand who can do
what across projects, reduces divergence, and increases interoperability.

The below sections explain how these new defaults in the Cyborg can solve the
issues mentioned above and extend more functionality to end users in a safe
and secure way.

More information is provided in the `cyborg specification <https://specs.openstack.org/openstack/cyborg-specs/specs/ussuri/approved/policy-defaults-refresh.html>`__

Scope
-----

OpenStack Keystone supports different scopes in tokens.
These are described `here <https://docs.openstack.org/keystone/latest//admin/tokens-overview.html#authorization-scopes>`__.
Token scopes represent the layer of authorization. Policy ``scope_types``
represent the layer of authorization required to access an API.

.. note::

     The ``scope_type`` of each policy is hardcoded and is not
     overridable via the policy file.

Cyborg policies have implemented the scope concept by defining the
``scope_type`` in policies. To know each policy's ``scope_type``, please
refer to the :doc:`Policy Reference <policy>` and look for
``Scope Types`` or ``Intended scope(s)`` in
:doc:`Policy Sample File <sample-policy>` as shown in below
examples.

.. rubric:: ``system`` scope

Policies with a ``scope_type`` of ``system`` means a user with a
``system-scoped`` token has permission to access the resource. This can be
seen as a global role. All the system-level operation's policies
have defaulted to ``scope_type`` of ``['system']``.

For example, consider the ``POST  /v2/device_profiles`` API.

.. code::

    # Create a device_profile
    # POST  /v2/device_profiles
    # Intended scope(s): system
    #"cyborg:device_profile:create": "rule:system_admin_api"

.. rubric:: ``project`` scope

Policies with a ``scope_type`` of ``project`` means a user with a
``project-scoped`` token has permission to access the resource. This can be
seen as a project role. All the project-level operation's policies should be
set to ``scope_type`` of ``['project']`` by default.

.. rubric:: ``system and project`` scope

Policies with a ``scope_type`` of ``system and project`` means a user with a
``system-scoped`` or ``project-scoped`` token has permission to access the
resource. All the system and project level operation's policies have defaulted
to ``scope_type`` of ``['system', 'project']``.

For example, consider the ``GET  /v2/device_profiles/{device_profiles_uuid}``
API.

.. code::

    # Retrieve a specific device_profile
    # GET  /v2/device_profiles/{device_profiles_uuid}
    # Intended scope(s): system, project
    #"cyborg:device_profile:get_one": "rule:system_or_project_reader"

These scope types provide a way to differentiate between system-level and
project-level access roles. You can control the information with scope of the
users.

Policy scope is disabled by default to allow operators to migrate from
the old policy enforcement system in a graceful way. This can be
enabled by configuring the :oslo.config:option:`oslo_policy.enforce_scope`
option to ``True``.

.. note::

  [oslo_policy]
  enforce_scope=True


Roles
-----

You can refer to `this <https://docs.openstack.org/keystone/latest//admin/service-api-protection.html>`__
document to know about all available defaults from Keystone.

Along with the ``scope_type`` feature, Cyborg policy defines new
defaults for each policy.

.. rubric:: ``reader``

This provides read-only access to the resources within the ``system`` or
``project``. Cyborg policies are defaulted to below rules:

.. code::

   system_reader_api
      Default
         role:reader and system_scope:all

   project_reader_api
      Default
         role:reader and project_id:%(project_id)s

   system_or_project_reader
      Default
         rule:system_reader_api or rule:project_reader_api

.. rubric:: ``member``

This role is to perform the project level write operation with combination
to the system admin. Cyborg policies are defaulted to below rules:

.. code::

   project_member_api
      Default
         role:member and project_id:%(project_id)s

   system_admin_or_owner
      Default
         rule:system_admin_api or rule:project_member_api

.. rubric:: ``admin``

This role is to perform the admin level write operation at system as well
as at project-level operations. Cyborg policies are defaulted to below rules:

.. code::

   system_admin_api
      Default
         role:admin and system_scope:all

   project_admin_api
      Default
         role:admin and project_id:%(project_id)s

   system_admin_or_owner
      Default
         rule:system_admin_api or rule:project_member_api

With these new defaults, you can solve the problem of:

#. Providing the read-only access to the user. Polices are made more granular
   and defaulted to reader rules. For exmaple: If you need to let someone audit
   your deployment for security purposes.

#. Customize the policy in better way. For example, you will be able
   to provide access to project level member to perform arq patch/post for
   instance boot with the project's token.

Backward Compatibility
----------------------

During the development period (Victoria and Wallaby releases), the new and old
policy will both work for backward compatibility by supporting the old
defaults and disabling the ``scope_type`` feature by default. This means the
old defaults and deployments that use them will keep working as-is. However,
we encourage every deployment to switch to new policy. ``scope_type`` will be
enabled by default and the old defaults will be removed starting in the
X release.

To implement the new default reader roles, some policies needed to become
granular. They have been renamed, with the old names still supported for
backwards compatibility.

Migration Plan
--------------

To have a graceful migration, Cyborg provides two flags to switch to the new
policy completely. You do not need to overwrite the policy file to adopt the
new policy defaults.

Here is step wise guide for migration:

#. Create scoped token:

   You need to create the new token with scope knowledge via below CLI:

   - `Create System Scoped Token <https://docs.openstack.org/keystone/latest//admin/tokens-overview.html#operation_create_system_token>`__.
   - `Create Project Scoped Token <https://docs.openstack.org/keystone/latest//admin/tokens-overview.html#operation_create_project_scoped_token>`__.

#. Create new default roles in keystone if not done:

   If you do not have new defaults in Keystone then you can create and re-run
   the `Keystone Bootstrap <https://docs.openstack.org/keystone/latest//admin/bootstrap.html>`__.
   Keystone added this support in 14.0.0 (Rocky) release.

#. Enable Scope Checks

   The :oslo.config:option:`oslo_policy.enforce_scope` flag is to enable the
   ``scope_type`` features. The scope of the token used in the request is
   always compared to the ``scope_type`` of the policy. If the scopes do not
   match, one of two things can happen.
   If :oslo.config:option:`oslo_policy.enforce_scope` is True, the request
   will be rejected. If :oslo.config:option:`oslo_policy.enforce_scope` is
   False, an warning will be logged, but the request will be accepted
   (assuming the rest of the policy passes). The default value of this flag
   is False.

   .. note:: Before you enable this flag, you need to audit your users and make
             sure everyone who needs system-level access has a system role
             assignment in keystone.

#. Enable new defaults

   The `oslo_policy.enforce_new_defaults` flag switches
   the policy to new defaults-only. This flag controls whether or not to use
   old deprecated defaults when evaluating policies. If True, the old
   deprecated defaults are not evaluated. This means if any existing
   token is allowed for old defaults but is disallowed for new defaults,
   it will be rejected. The default value of this flag is False.

   .. note:: Before you enable this flag, you need to educate users about the
             different roles they need to use to continue using Cyborg APIs.


#. Check for deprecated policies

   A few policies were made more granular to implement the reader roles. New
   policy names are available to use. If old policy names which are renamed
   are overwritten in policy file, then warning will be logged. Please migrate
   those policies to new policy names.

We expect all deployments to migrate to new policy by X release so that
we can remove the support of old policies.
