===============
Cyborg REST API
===============

Cyborg introduced and landed a totally `new DB modeling schema
<https://specs.openstack.org/openstack/cyborg-specs/specs/stein/approved/cyborg-database-model-proposal.html>`_
for tracking cyborg resources in Stein release. The legacy v1 api does not
match the new data model, which we changed pretty much, so cyborg starts to
support a new set of api(v2) as well.

v2.0
-----
The Train release introduced version 2.0 APIs. Details of these APIs
can be found `here
<https://specs.openstack.org/openstack/cyborg-specs/specs/train/approved/cyborg-api.html>`_.
However, Train release landed partial V2 APIs, which means incomplete. One can
expect full support V2 APIs (as well as full V2 API documentation) from cyborg
in the Ussuri release.

The supported V2 APIs in Train are listed below.
The URIs are relative to ``http://<controller-ip>/accelerator/v2``.


.. list-table::
   :widths: 10 40 50
   :header-rows: 1

   * - Verb
     - URI
     - Description
   * - GET
     - ``/device_profiles``
     - List all device profiles
   * - GET
     - ``/device_profiles/{uuid}``
     - Retrieve a certain device profile info identified by `{uuid}`
   * - POST
     - ``/device_profiles``
     - Create a new device profile
   * - DELETE
     - ``/device_profiles/{uuid}``
     - Delete the device_profile identified by `{uuid}`
   * - DELETE
     - ``/device_profiles?value={device_profile_name1},{device_profile_name2}``
     - Delete the device_profiles identified by `{name}`
   * - GET
     - ``/accelerator_requests``
     - List Accelerator Requests
   * - GET
     - ``/accelerator_requests/{accelerator_request_uuid}``
     - Get one Accelerator Requests
   * - POST
     - ``/accelerator_requests``
     - Create Accelerator Requests
   * - PATCH
     - ``/accelerator_requests/{accelerator_request_uuid}``
     - Update Accelerator Requests
   * - DELETE
     - ``/accelerator_requests?arqs={accelerator_request_uuid}``
     - Delete the accelerator_requests identified by `{ARQ_uuid}`
   * - DELETE
     - ``/accelerator_requests?instance={instance_uuid}``
     - Delete the accelerator_requests identified by `{instance_uuid}`

v1.0
-----

The following v1 APIs are deprecated in Train and will be removed in the Ussuri
release.

The URIs are relative to ``http://<controller-ip>/accelerator/v1``.

.. list-table::
   :widths: 10 40 50
   :header-rows: 1

   * - Verb
     - URI
     - Description
   * - GET
     - ``/accelerators``
     - Return a list of accelerators
   * - GET
     - ``/accelerators/{uuid}``
     - Retrieve a certain accelerator info identified by `{uuid}`
   * - POST
     - ``/accelerators``
     - Create a new accelerator
   * - PUT
     - ``/accelerators/{uuid}``
     - Update the spec for the accelerator identified by `{uuid}`
   * - DELETE
     - ``/accelerators/{uuid}``
     - Delete the accelerator identified by `{uuid}`
   * - GET
     - ``/accelerators/deployables/``
     - Return a list of deployables
   * - GET
     - ``/accelerators/deployables/{uuid}``
     - Retrieve a certain deployable info identified by `{uuid}`
   * - POST
     - ``/accelerators/deployables/``
     - Create a new deployable
   * - PATCH
     - ``/accelerators/deployables/{uuid}/program``
     - Program a new deployable(FPGA)
   * - PATCH
     - ``/accelerators/deployables/{uuid}``
     - Update the spec for the deployable identified by `{uuid}`
   * - DELETE
     - ``/accelerators/deployables/{uuid}``
     - Delete the deployable identified by `{uuid}`

