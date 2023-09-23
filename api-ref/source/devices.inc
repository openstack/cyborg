.. -*- rst -*-
.. needs:body_verification

Devices
+++++++

Lists, shows details for devices. Enable or disable for a device.

A `device` represent a physical card like FPGA card or GPU card.

List Devices
------------

.. rest_method:: GET /v2/devices

Lists UUIDs, names, type and more informations for all devices.

Normal response codes: 200

Error response codes: unauthorized(401), forbidden(403)

Request
=======
.. rest_parameters:: parameters.yaml

  - type: device_type
  - vendor: device_vendor
  - hostname: hostname
  - filters: device_filters

Response
========
.. rest_parameters:: parameters.yaml

  - devices: devices
  - uuid: device_uuid_resp
  - type: device_type_resp
  - vendor: device_vendor_resp
  - model: device_model_resp
  - std_board_info: device_std_board_info_resp
  - vendor_board_info: device_vendor_board_info_resp
  - hostname: hostname_resp
  - status: device_status_resp
  - created_at: created
  - updated_at: updated
  - links: links

**Example response: list all devices**

.. literalinclude:: ../../doc/api_samples/devices/devices-list-resp.json
   :language: javascript

Get One Device
--------------

.. rest_method:: GET /v2/devices/{device_uuid}

Gets the UUID, name, type and more informations for one device with the specified UUID.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403), notfound(404)

Request
=======
.. rest_parameters:: parameters.yaml

  - device_uuid: device_uuid

Response
========
.. rest_parameters:: parameters.yaml

  - uuid: device_uuid_resp
  - type: device_type_resp
  - vendor: device_vendor_resp
  - model: device_model_resp
  - std_board_info: device_std_board_info_resp
  - vendor_board_info: device_vendor_board_info_resp
  - hostname: hostname_resp
  - status: device_status_resp
  - created_at: created
  - updated_at: updated
  - links: links

**Example response: show details of a specific device**

.. literalinclude:: ../../doc/api_samples/devices/devices-getone-resp.json
   :language: javascript

Enable a device
---------------

.. rest_method:: POST /v2/devices/{device_uuid}/enable

Set the device to enabled status.

Normal response codes: 200

Error response codes: 404(the device is not found),403(the role is not admin)

Request
=======
.. rest_parameters:: parameters.yaml

  - device_uuid: device_uuid

Response
========
There is no body content for the response of a successful request.

Disable a device
----------------

.. rest_method:: POST /v2/devices/{device_uuid}/disable

Set the device to maintaining status.

Normal response codes: 200

Error response codes: 404(the device is not found),403(the role is not admin)

Request
=======
.. rest_parameters:: parameters.yaml

  - device_uuid: device_uuid

Response
========
There is no body content for the response of a successful request.