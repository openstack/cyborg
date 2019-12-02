REST API Version History
========================

This documents the changes made to the REST API with every
microversion change. The description for each version should be a
verbose one which has enough information to be suitable for use in
user documentation.

2.0
---

This is the initial version of the v2 API which supports
microversions.

A user can specify a header in the API request::

  OpenStack-API-Version: accelerator <microversion>

where ``<microversion>`` is any valid api microversion for this API.

If no version is specified then the API will behave as if a version
request of v2.0 was requested.
