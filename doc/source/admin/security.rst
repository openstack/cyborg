========
Security
========

This guide describes security-relevant behavior and configuration for Cyborg
operators. Keep Cyborg, Nova, and Keystone integration aligned with your
cloud's support matrix and release notes for any upgrade-specific steps.

ARQ ownership and project scoping
---------------------------------

Accelerator requests (ARQs) are scoped to the project of the user who
created them. The ``project_id`` field on each ARQ record tracks ownership.

Non-admin users can only list, view, and delete their own project's ARQs.
Admin users can see all ARQs across all projects.

Service token requirement
-------------------------

Operations on bound ARQs — those with an ``instance_uuid`` set — require
a valid service token in addition to the user token. This ensures that
only Nova can bind, unbind, or delete ARQs that are attached to running
instances, preventing users from directly manipulating instance-level
accelerator state.

The following operations require a service token:

* Setting ``instance_uuid`` on an ARQ (binding)
* Clearing ``instance_uuid`` on an ARQ (unbinding)
* Deleting an ARQ that has ``instance_uuid`` set

Unbound ARQs (no ``instance_uuid``) can be deleted by their owner without
a service token.

.. note::

    In a future release, when Cyborg adopts secure RBAC (SRBAC), the
    ``service`` role may be enforced on the user token itself for
    binding, unbinding, and mutating bound ARQs. This would replace
    the current service token check with standard policy-based
    enforcement.

Configuration
~~~~~~~~~~~~~

Nova must be configured to send service tokens to Cyborg:

.. code-block:: ini

    # /etc/nova/nova.conf
    [service_user]
    send_service_user_token = true
    auth_url = <keystone_url>
    auth_type = password
    project_domain_name = Default
    project_name = service
    user_domain_name = Default
    username = nova
    password = <password>

Cyborg defaults ``service_token_roles_required`` to ``true`` so that
keystonemiddleware validates the service token roles. Operators should
not disable this:

.. code-block:: ini

    # /etc/cyborg/cyborg.conf  (defaults shown — no change needed)
    [keystone_authtoken]
    service_token_roles_required = true   # Cyborg default
    service_token_roles = service         # keystonemiddleware default

.. warning::

    Do not set ``service_token_roles_required = false``. Doing so
    disables keystonemiddleware's validation of the service token
    roles. Cyborg still enforces the service role requirement in
    code, but disabling middleware validation removes a layer of
    defence-in-depth.

Policy and tokens
-----------------

Cyborg API policies are evaluated in a **project-scoped** context for
user-facing accelerator management. Rely on project-scoped credentials
for administrative tasks; system-scoped tokens are not appropriate for
these APIs.

For detailed upgrade ordering (schema migrations, online data migrations,
and service restarts), see :doc:`upgrade`.
