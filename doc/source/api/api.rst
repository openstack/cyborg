===============
Cyborg REST API
===============

v2.0
-----
The Train release introduces version 2.0 APIs. Details of these APIs
can be found `here
<https://opendev.org/openstack/cyborg-specs/src/branch/master/specs/train/approved/cyborg-api.rst>`_.


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
