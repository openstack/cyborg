REST API Version History
========================

This documents the changes made to the REST API with every
microversion change. The description for each version should be a
verbose one which has enough information to be suitable for use in
user documentation.

A user can specify a header in the API request::

  OpenStack-API-Version: accelerator <microversion>

where ``<microversion>`` is any valid api microversion for this API.

If no version is specified then the API will behave as if a version
request of v2.0 was requested.

2.0
---

This is the initial version of the v2 API which supports
microversions.

.. _microversion 2.1:

2.1 (Maximum in Victoria)
-------------------------

Add ``project_id`` for Accelerator Requests PATCH API. ``project_id`` is
used to control the operation of arq with different roles.

2.2
---

Changed ``device_profile_uuid`` to ``device_profile_name_or_uuid`` in
`Get One Device Profile` API path, so support getting device profile by
name (newly introduced) and uuid.

 - GET /v2/device_profiles/{device_profile_name_or_uuid}

2.3
---

Add new status info for list Device and get device API.

 - GET: /devices
 - GET: /devices/{uuid}
