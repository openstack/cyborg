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

Error response codes: unauthorized(401), forbidden(403)

**Example response: list all deployables**

.. literalinclude:: ../../../doc/api_samples/deployables/deployables-list-resp.json
   :language: javascript

Get One Deployable
------------------

.. rest_method:: GET /v2/deployables/{deployable_uuid}

Gets the UUID, name, attribute list and more informations for one deployable with the specified UUID.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403)

Request
=======
.. rest_parameters:: parameters.yaml

  - deployable_uuid: deployable_uuid

**Example response: show details of a specific deployable**

.. literalinclude:: ../../../doc/api_samples/deployables/deployables-getone-resp.json
   :language: javascript
