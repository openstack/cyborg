.. -*- rst -*-
.. needs:body_verification

Devices
+++++++

Lists, shows details for devices.

A `device` represent a physical card like FPGA card or GPU card.

List Devices
------------

.. rest_method:: GET /v2/devices

Lists UUIDs, names, type and more informations for all devices.

Normal response codes: 200

Error response codes: unauthorized(401), forbidden(403)

**Example response: list all devices**

.. literalinclude:: ../../../doc/api_samples/devices/devices-list-resp.json
   :language: javascript

Get One Device
--------------

.. rest_method:: GET /v2/devices/{device_uuid}

Gets the UUID, name, type and more informations for one device with the specified UUID.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403)

Request
=======
.. rest_parameters:: parameters.yaml

  - device_uuid: device_uuid

**Example response: show details of a specific device**

.. literalinclude:: ../../../doc/api_samples/devices/devices-getone-resp.json
   :language: javascript
