.. -*- rst -*-
.. needs:body_verification

Deployables
+++++++++++

Lists, shows details for deployables.

A `deployables` represent a logical unit of an acceleration card, such as re-configurable
region of an FPGA card.

List Deployables
----------------

.. rest_method:: GET /v2/deployables

Lists UUIDs, names, attribute list and more informations for all deployables.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403), internalServerError(500)

Request
=======
.. rest_parameters:: parameters.yaml

   - filters: filters

Response
========
.. rest_parameters:: parameters.yaml

  - deployables: deployables
  - uuid: deployable_uuid_resp
  - parent_id: deployable_parent_id
  - root_id: deployable_root_id
  - name: deployable_name
  - num_accelerators: deployable_num_accelerators
  - device_id: deployable_device_id
  - attributes_list: deployable_attributes_list
  - rp_uuid: deployable_rp_uuid
  - driver_name: deployable_driver_name
  - bitstream_id: deployable_bitstream_id
  - created_at: created
  - updated_at: updated
  - links: links

**Example response: list all deployables**

.. literalinclude:: ../../doc/api_samples/deployables/deployables-list-resp.json
   :language: javascript

Get One Deployable
------------------

.. rest_method:: GET /v2/deployables/{deployable_uuid}

Gets the UUID, name, attribute list and more informations for one deployable with the specified UUID.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403), notfound(404)

Request
=======
.. rest_parameters:: parameters.yaml

  - deployable_uuid: deployable_uuid

Response
========
.. rest_parameters:: parameters.yaml

  - uuid: deployable_uuid_resp
  - parent_id: deployable_parent_id
  - root_id: deployable_root_id
  - name: deployable_name
  - num_accelerators: deployable_num_accelerators
  - device_id: deployable_device_id
  - attributes_list: deployable_attributes_list
  - rp_uuid: deployable_rp_uuid
  - driver_name: deployable_driver_name
  - bitstream_id: deployable_bitstream_id
  - created_at: created
  - updated_at: updated
  - links: links

**Example response: show details of a specific deployable**

.. literalinclude:: ../../doc/api_samples/deployables/deployables-getone-resp.json
   :language: javascript
