.. -*- rst -*-
.. needs:body_verification

Device Profiles
+++++++++++++++

Lists, creates, shows details for, updates and deletes device profiles.

A `device_profile 
<http://specs.openstack.org/openstack/cyborg-specs/specs/train/approved/device-profiles.html>`_
is a named set of the user requirements for one or more
accelerators. It can be viewed as a flavor for devices. Broadly it includes
two things: the desired amounts of specific resource classes and the
requirements that the resource provider(s) must satisfy. While the resource
classes are the same as those known to Placement, some requirements would
correspond to Placement traits and others to properties that Cyborg alone
knows about.


List Device Profiles
--------------------

.. rest_method:: GET /v2/device_profiles

Lists UUIDs, names, groups for all device profiles.

Normal response codes: 200

Error response codes: unauthorized(401), forbidden(403)

**Example response: list all device profiles**

.. literalinclude:: ../../../doc/api_samples/device_profiles/device_profiles-list-resp.json
   :language: javascript

Get One Device Profile
----------------------

.. rest_method:: GET /v2/device_profiles/{device_profile_uuid}

Gets the UUID, name, groups for one device_profile with the specified UUID.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403)

Request
=======
.. rest_parameters:: parameters.yaml

  - device_profile_uuid: device_profile_uuid

**Example response: get details of a specific device profile**

.. literalinclude:: ../../../doc/api_samples/device_profiles/device_profiles-getone-resp.json
   :language: javascript

Create Device Profile
---------------------

.. rest_method:: POST /v2/device_profiles

Creates a device profile. The payload should have these fields:

Normal response codes: 201

Error response codes: badRequest(400), unauthorized(401), forbidden(403),
conflict(409)

Request
=======
.. rest_parameters:: parameters.yaml

  - name: device_prof_name_req
  - groups: device_prof_groups_req

**Example post curl with resource/trait**

.. literalinclude:: ../../../doc/api_samples/device_profiles/device_profiles-post-curl.json
   :language: javascript

**Example post curl with a cyborg property when bitstream is required**

.. literalinclude:: ../../../doc/api_samples/device_profiles/device_profiles-post-curl-with-bitstream.json
   :language: javascript

**Example response: create a device profile**

.. literalinclude:: ../../../doc/api_samples/device_profiles/device_profiles-create-resp.json
   :language: javascript

Delete One Device Profile by uuid
---------------------------------

.. rest_method:: DELETE /v2/device_profiles/{device_profile_uuid}

Delete a device profile. No query parameters required.

Delete Multiple Device Profiles by names
----------------------------------------

.. rest_method:: DELETE /v2/device_profiles?value={device_profile_name1},{device_profile_name2}

In the URL, Device profiles to be deleted should be in comma-delimited list of
device profile names.

.. note::
   Today we do not allow deletion of a device profile when it is in use by
   VMs, because ARQs have a foreign key on device profile table. But we copy
   the device profile groups into the ARQ, so this foreign key is not needed.
   So we can improve in Ussuri.

Response
========

Normal response codes: 204

There is no body content for the response of a successful DELETE query
