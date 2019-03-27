.. -*- rst -*-
.. needs:body_verification

Deployables
+++++++++++

Lists, creates, shows details for, updates and deletes deployables.

A deployable is a component of a device that contains accelerators.
(An accelerator is a hardware resource that offload computation; it
is the smallest unit within a device that can be assigned to a VM.)

.. note::

   In the following example url requests $cyborg_endpoint_url can be
   different depending on how cyborg-api service is running. If cyborg-api
   service is running as a python process, use "http://localhost:6666/v1",
   otherwise if cyborg-api is running as a WSGI application:
   "https://docs.openstack.org/cyborg/latest/admin/config-wsgi.html",
   use "http://localhost/accelerator/v1".

List Deployables
----------------

.. rest_method:: GET /deployables

Lists UUIDs, names, number of accelerators, device_ids and root_ids,
parent_ids for all deployables.

Supported query parameters:

  - limit: Optional, to determinate maximum number of accelerators to return.
  - marker: Optional, to display a list of accelerators after this marker.
  - sort_key: Optional, to sort the returned deployables list by this
              specified key value.
  - sort_dir: Optional, to return the deployables list with sort direction.

**Example response: list deployables**

.. literalinclude:: ../../../doc/api_samples/deployables/deployables-list-resp.json
   :language: javascript

Get One Deployable
------------------

.. rest_method:: GET /deployables/uuid

Gets the UUID, name, number of accelerators and other fields
for one deployable with the specified UUID.

Gets a deployable. The payload should have these fields:

  - uuid: UUID

**Example response: get details of a specific deployable**

.. literalinclude:: ../../../doc/api_samples/deployables/deployables-getone-resp.json

Create Deployable
-----------------

.. rest_method:: POST /deployables

Creates a deployable. The payload should have these fields:

  - uuid: UUID
  - name: string
  - num_accelerators: integer
  - address: string
  - interface_type: string
  - assignable: boolean
  - availability: string
  - accelerator_id: integer

**Example post curl**

.. literalinclude:: ../../../doc/api_samples/deployables/deployable-post-curl.json

**Example response: create a deployable**

.. literalinclude:: ../../../doc/api_samples/deployables/deployable-create-resp.json

Update Deployable
-----------------

.. rest_method:: PATCH /deployables/uuid

Update a deployable. The payload should be a RFC 6902-compliant
JSON patch, FYR:"http://jsonpatch.com/".
The patch should have these fields:

  - uuid: UUID

Other fields are optional.

**Example patch curl**

.. literalinclude:: ../../../doc/api_samples/deployables/deployable-patch-curl.json

**Example response: update a deployable**

.. literalinclude:: ../../../doc/api_samples/deployables/deployable-update-resp.json

Delete Deployable
-----------------

.. rest_method:: DELETE /deployables/uuid

Delete a deployable. No query parameters required.

Response will be like the following:

    .. code-block:: bash

        HTTP/1.1 204 No Content
        Date: Sat, 30 Mar 2019 09:51:49 GMT
        Server: Apache/2.4.29 (Ubuntu)
        x-openstack-request-id: req-46603a01-f04d-40b6-922f-2f2ec1201725
        Connection: close
