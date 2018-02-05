..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===================
Cyborg API proposal
===================

https://blueprints.launchpad.net/openstack-cyborg/+spec/cyborg-api

This spec proposes to provide the initial API design for Cyborg.

Problem description
===================

Cyborg as a common management framework for dedicated devices (hardware/
software accelerators, high-speed storage, etc) needs RESTful API to expose
the basic functionalities.

Use Cases
---------

* As a user I want to be able to spawn VM with dedicated hardware, so
that I can utilize provided hardware.
* As a compute service I need to know how requested resource should be
attached to the VM.
* As a scheduler service I'd like to know on which resource provider
requested resource can be found.

Proposed change
===============

In general we want to develop the APIs that support basic life cycle management
for Cyborg.

Life Cycle Management Phases
----------------------------

For cyborg, LCM phases include typical create, retrieve, update, delete operations.
One thing should be noted that deprovisioning mainly refers to detach(delete) operation
which deactivate an acceleration capability but preserve the resource itself
for future usage. For Cyborg, from functional point of view, the LCM includes provision,
attach,update,list, and detach. There is no notion of deprovisioning for Cyborg API
in a sense that we decomission or disconnect an entire accelerator device from
the bus.

Difference between Provision and Attach/Detach
----------------------------------------------

Noted that while the APIs support provisioning via CRUD operations, attach/detach
are considered different:

* Provision operations (create) will involve api->
conductor->agent->driver workflow, where as attach/detach (update/delete) could be taken
care of at the driver layer without the involvement of the pre-mentioned workflow. This
is similar to the difference between create a volume and attach/detach a volume in Cinder.

* The attach/detach in Cyborg API will mainly involved in DB status modification.

Difference between Attach/Detach To VM and Host
-----------------------------------------------

Moreover there are also differences when we attach an accelerator to a VM or
a host, similar to Cinder.

* When the attachment happens to a VM, we are expecting that Nova could call
the virt driver to perform the action for the instance. In this case Nova
needs to support the acc-attach and acc-detach action.

* When the attachment happens to a host, we are expecting that Cyborg could
take care of the action itself via Cyborg driver. Althrough currently there
is the generic driver to accomplish the job, we should consider a os-brick
like standalone lib for accelerator attach/detach operations.

Alternatives
------------

* For attaching an accelerator to a VM, we could let Cyborg perform the action
itself, however it runs into the risk of tight-coupling with Nova of which Cyborg
needs to get instance related information.
* For attaching an accelerator to a host, we could consider to use Ironic drivers
however it might not bode well with the standalone accelerator rack scenarios where
accelerators are not attached to server at all.

Data model impact
-----------------

A new table in the API database will be created::

    CREATE TABLE accelerators (
        accelerator_id INT NOT NULL,
        device_type STRING NOT NULL,
        acc_type STRING NOT NULL,
        acc_capability STRING NOT NULL,
        vendor_id STRING,
        product_id STRING,
        remotable INT,
    );

Note that there is an ongoing discussion on nested resource
provider new data structures that will impact Cyborg DB imp-
lementation. For code implementation it should be aligned
with resource provider db requirement as much as possible.


REST API impact
---------------

The API changes add resource endpoints to:

* `GET` a list of all the accelerators
* `GET` a single accelerator for a given id
* `POST` create a new accelerator resource
* `PUT` an update to an existing accelerator spec
* `PUT` attach an accelerator to a VM or a host
* `DELETE` detach an existing accelerator for a given id

The following new REST API call will be created:

'GET /accelerators'
*************************

Return a list of accelerators managed by Cyborg

Example message body of the response to the GET operation::

    200 OK
    Content-Type: application/json

    {
       "accelerator":[
        {
          "uuid":"8e45a2ea-5364-4b0d-a252-bf8becaa606e",
          "acc_specs":
          {
             "remote":0,
             "num":1,
             "device_type":"CRYPTO"
             "acc_capability":
             {
                "num":2
                "ipsec":
                {
                   "aes":
                   {
                      "3des":50,
                      "num":1,
                   }
                }
             }
           }
         },
         {
           "uuid":"eaaf1c04-ced2-40e4-89a2-87edded06d64",
           "acc_specs":
           {
              "remote":0,
              "num":1,
              "device_type":"CRYPTO"
              "acc_capability":
              {
                 "num":2
                 "ipsec":
                 {
                    "aes":
                    {
                       "3des":40,
                       "num":1,
                    }
                 }
              }
            }
          }
       ]
    }

'GET /accelerators/{uuid}'
*************************

Retrieve a certain accelerator info indetified by '{uuid}'

Example GET Request::

    GET /accelerators/8e45a2ea-5364-4b0d-a252-bf8becaa606e

    200 OK
    Content-Type: application/json

    {
       "uuid":"8e45a2ea-5364-4b0d-a252-bf8becaa606e",
       "acc_specs":{
          "remote":0,
          "num":1,
          "device_type":"CRYPTO"
          "acc_capability":{
             "num":2
             "ipsec":{
                 "aes":{
                   "3des":50,
                   "num":1,
                 }
             }
          }
        }
    }

If the accelerator does not exist a `404 Not Found` must be
returned.

'POST /accelerators/{uuid}'
*******************

Create a new accelerator

Example POST Request::

    Content-type: application/json

    {
        "name": "IPSec Card",
        "uuid": "8e45a2ea-5364-4b0d-a252-bf8becaa606e"
    }

The body of the request must match the following JSONSchema document::

    {
        "type": "object",
        "properties": {
            "name": {
                "type": "string"
            },
            "uuid": {
                "type": "string",
                "format": "uuid"
            }
        },
        "required": [
            "name"
        ]
        "additionalProperties": False
    }

The response body is empty. The headers include a location header
pointing to the created accelerator resource::

    201 Created
    Location: /accelerators/8e45a2ea-5364-4b0d-a252-bf8becaa606e

A `409 Conflict` response code will be returned if another accelerator
exists with the provided name.

'PUT /accelerators/{uuid}/{acc_spec}'
*************************

Update the spec for the accelerator identified by `{uuid}`.

Example::

    PUT /accelerator/8e45a2ea-5364-4b0d-a252-bf8becaa606e

    Content-type: application/json

    {
        "acc_specs":{
           "remote":0,
           "num":1,
           "device_type":"CRYPTO"
           "acc_capability":{
              "num":2
              "ipsec":{
                 "aes":{
                   "3des":50,
                   "num":1,
                 }
              }
           }
         }
    }

The returned HTTP response code will be one of the following:

* `200 OK` if the spec is successfully updated
* `404 Not Found` if the accelerator identified by `{uuid}` was
  not found
* `400 Bad Request` for bad or invalid syntax
* `409 Conflict` if another process updated the same spec.


'PUT /accelerators/{uuid}'
*************************

Attach the accelerator identified by `{uuid}`.

Example::

    PUT /accelerator/8e45a2ea-5364-4b0d-a252-bf8becaa606e

    Content-type: application/json

    {
        "name": "IPSec Card",
        "uuid": "8e45a2ea-5364-4b0d-a252-bf8becaa606e"
    }

The returned HTTP response code will be one of the following:

* `200 OK` if the accelerator is successfully attached
* `404 Not Found` if the accelerator identified by `{uuid}` was
  not found
* `400 Bad Request` for bad or invalid syntax
* `409 Conflict` if another process attach the same accelerator.


'DELETE /accelerator/{uuid}'
****************************

Detach the accelerator identified by `{uuid}`.

The body of the request and the response is empty.

The returned HTTP response code will be one of the following:

* `204 No Content` if the request was successful and the accelerator was detached.
* `404 Not Found` if the accelerator identified by `{uuid}` was
  not found.
* `409 Conflict` if there exist allocations records for any of the
  accelerator resource that would be detached as a result of detaching the accelerator.


Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

None

Performance Impact
------------------

None

Other deployer impact
---------------------

None

Developer impact
----------------

Developers can use this REST API after it has been implemented.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  zhipengh <huangzhipeng@huawei.com>

Work Items
----------

* Implement the APIs specified in this spec
* Proposal to Nova about the new accelerator
attach/detach api
* Implement the DB specified in this spec


Dependencies
============

None.

Testing
=======

* Unit tests will be added to Cyborg API.

Documentation Impact
====================

None

References
==========

None

History
=======


.. list-table:: Revisions
   :header-rows: 1

   * - Release
     - Description
   * - Pike
     - Introduced
