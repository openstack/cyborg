.. -*- rst -*-
.. needs:body_verification

Accelerator Requests
++++++++++++++++++++

Lists, creates, shows details for, updates and deletes accelerator requests.

An accelerator request (ARQ) represents a request for a single accelerator
to be assigned to an instance. ARQs are created in accordance with the
resource_groups defined in a `device_profile 
<http://specs.openstack.org/openstack/cyborg-specs/specs/train/approved/device-profiles.html>`_
by the operator. The accelerator request in the user request may have N
request groups, each asking for M accelerators; then N * M ARQs will be
created for that accelerator request.

List Accelerator Requests
-------------------------

.. rest_method:: GET /v2/accelerator_requests

Lists host_name, device_rp_uuid, instance_uuid and device_profile_group_id
for all accelerator_requests.

**Example response: list all accelerator requests**

.. literalinclude:: ../../../doc/api_samples/accelerator_requests/accelerator_requests-list-resp.json
   :language: javascript

Get One Accelerator Request
---------------------------

.. rest_method:: GET /v2/accelerator_requests/{accelerator_request_uuid}

Gets host_name, device’s_RP_UUID, instance UUID and device_profile_group_ID
for one accelerator request with the specified UUID.

Request
=======
.. rest_parameters:: parameters.yaml

  - accelerator_request_uuid: accelerator_request_uuid 

**Example response: get details of a specific accelerator request**

.. literalinclude:: ../../../doc/api_samples/accelerator_requests/accelerator_requests-getone-resp.json

Create Accelerator Requests
---------------------------

.. rest_method:: POST /v2/accelerator_requests

Creates an accelerator request. The payload should have the following field:

Request
=======
.. rest_parameters:: parameters.yaml

  - device_profile_name: device_profile_name

**Example post curl**

.. literalinclude:: ../../../doc/api_samples/accelerator_requests/accelerator_requests-post-curl.json

**Example response: create an accelerator request**

.. literalinclude:: ../../../doc/api_samples/accelerator_requests/accelerator_requests-create-resp.json

Update Accelerator Requests
---------------------------

The Nova compute manager calls the Cyborg API PATCH /v2/accelerator_requests
to bind and unbind the ARQ with the host name, device’s RP UUID and instance UUID. This
is an asynchronous call which prepares or reconfigures the device in the
background.

.. rest_method:: PATCH /v2/accelerator_requests/{accelerator_request_uuid}

Updates:an accelerator request. The payload should have these fields:

Request
=======
.. rest_parameters:: parameters.yaml

  - accelerator_request_uuid: accelerator_request_uuid
  - hostname: hostname_bind_unbind_req
  - device_rp_uuid: device_rp_uuid_bind_unbind_req 
  - instance_uuid: instance_uuid_bind_unbind_req

**Example patch curl**

.. literalinclude:: ../../../doc/api_samples/accelerator_requests/accelerator_requests-patch-curl.json

**Example response: update an accelerator request**

.. literalinclude:: ../../../doc/api_samples/accelerator_requests/accelerator_requests-update-resp.json

Delete Accelerator Requests by ARQ uuid
---------------------------------------

.. rest_method:: DELETE /v2/accelerator_requests?arqs={accelerator_request_uuid}

Delete Accelerator Requests by instance uuid
--------------------------------------------

.. rest_method:: DELETE /v2/accelerator_requests?instance={instance_uuid}

Delete an accelerator request. No query parameters required.

Response
========

Normal response codes: 204

There is no body content for the response of a successful DELETE query
