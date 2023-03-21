.. -*- rst -*-
.. needs:body_verification

Attributes
++++++++++

Lists, shows details, creates and deletes for attributes.

A `attribute` represents the trait of a physical card like FPGA or GPU.

List Attributes
---------------

.. rest_method:: GET /v2/attributes

Lists UUID, deployable_id, key, value and more information for all devices.

Normal response codes: 200

Error response codes: unauthorized(401), forbidden(403)

Request
=======
.. rest_parameters:: parameters.yaml

  - attribute_request_depid: attribute_request_depid

Response
========
.. rest_parameters:: parameters.yaml

  - attributes: attributes
  - uuid: attribute_uuid_resp
  - id: attribute_id_resp
  - deployable_id: attribute_deployable_id_resp
  - key: attribute_key_resp
  - value: attribute_value_resp
  - created_at: created
  - updated_at: updated
  - links: links

**Example response: list all attributes**

.. literalinclude:: ../../doc/api_samples/attributes/attributes-list-resp.json
   :language: javascript


Get One Attribute
-----------------

.. rest_method:: GET /v2/attributes/{attribute_uuid}

Gets the UUID, id, deployable_id, key, value and more information for one attribute with the specified UUID.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403), notfound(404)

Request
=======
.. rest_parameters:: parameters.yaml

  - attribute_uuid: attribute_request_uuid

Response
========
.. rest_parameters:: parameters.yaml

  - uuid: attribute_uuid_resp
  - id: attribute_id_resp
  - deployable_id: attribute_deployable_id_resp
  - key: attribute_key_resp
  - value: attribute_value_resp
  - created_at: created
  - updated_at: updated
  - links: links

**Example response: show details of a specific attribute**

.. literalinclude:: ../../doc/api_samples/attributes/attributes-getone-resp.json
   :language: javascript

Create Attributes
-----------------

.. rest_method:: POST /v2/attributes

Creates an attribute. The payload should have the following field:

Request
=======
.. rest_parameters:: parameters.yaml

  - deployable_id: attribute_deployable_id_req
  - key: attribute_key_req
  - value: attribute_value_req

**Example post curl**

.. literalinclude:: ../../doc/api_samples/attributes/attributes-post-curl.json

**Example response: create an attribute**

.. literalinclude:: ../../doc/api_samples/attributes/attributes-create-resp.json

Delete One Attribute by uuid
----------------------------

.. rest_method:: DELETE /v2/attributes/{attribute_uuid}

Delete an attribute. No query parameters required.
