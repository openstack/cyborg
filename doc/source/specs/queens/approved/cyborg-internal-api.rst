..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
       Cyborg Internal API spec
==========================================

This document loosely specifies the API calls between
the components of Cyborg. Driver, Agent, Conductor, and API endpoint.

These API's are internal and therefore may change from version to version
without warning or backwards compatibility. This document is kept as a
developer reference to be edited before any internally braking changes
are made.

Problem description
===================

Developers writing one component of Cyborg need to know how to talk to another
component of Cyborg, hopefully without having to go spelunking in the code
of that component.


Use Cases
---------

Happier Cyborg developers

Proposed change
===============

Versioning internal API's

Alternatives
------------

A mess

Data model impact
-----------------

A fixed internal API should help keep data models consistent.

REST API impact
---------------

The API changes add resource endpoints to:

Driver:

* `POST` start accelerator discovery FROM: Agent
* `GET` get a list of discovered accelerators and their properties FROM: Agent

Agent:

* `POST` register driver FROM: Driver
* `POST` start accelerator discovery across all drivers FROM: Conductor
* `GET` get a list of all accelerators across all drivers FROM: Conductor

Conductor:
* `POST` register agent FROM: Agent


The following new REST API call will be created:

Driver 'POST /discovery'
***************************

Trigger the discovery and setup process for a specific driver

.. code-block:: ini

    Content-Type: application/json

    {
       "status":"IN-PROGRESS"
    }

Driver 'GET /hardware'
**************************

Gets a list of hardware, not accelerators, accelerators are
ready to use entires available by the public API. Hardware are
physical devices on nodes that may or may not be ready to use or
even fully supported.

.. code-block:: ini

    200 OK
    Content-Type: application/json

    {
       "hardware":[
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
           "acc_status":
           {
             "setup_required":true,
             "reboot_equired":false
           }
         }]
    }


Driver 'POST /hello'
***************************

Registers that a driver has been installed on the machine and is ready to use.
As well as it's endpoint and hardware support.

.. code-block:: ini

    Content-Type: application/json

    {
       "status":"READY",
       "endpoint":"localhost:1337",
       "type":"CRYPTO"
    }

Agent 'POST /discovery'
***************************

Trigger the discovery and setup process for all registered drivers

See driver example


Agent 'GET /hardware'
***************************

Get list of hardware across all drivers on the node

see driver example


Conductor 'POST /hello'
***************************

Registers that an Agent has been installed on the machine and is ready to use.

.. code-block:: ini

    Content-Type: application/json

    {
       "status":"READY",
       "endpoint":"compute-whatever:1337",
    }


Security impact
---------------

Care must be taken to secure the internal endpoints from malicious calls


Notifications impact
--------------------

N/A

Other end user impact
---------------------

This change might have an impact on python-cyborgclient

Performance Impact
------------------

In this model the Agent takes care of wrangling however many drivers are on
a compute and the Conductor takes care of wrangling all the agents to present
a coherent answer to the API quickly and easily. I don't include
API <-> Conductor calls yet because I assume the API will be for the most part
working from the database while the Conductor tries to keep that database up to
date and takes the occasional setup call.


Other deployer impact
---------------------

In this model we won't really know when we're missing an agent. If one has
reported in previously and then goes away we can have an alarm for that. But
if an agent never reports in we just have to assume no instance exists by that
name. This means making sure the Cyborg Drivers/Agent's are installed and
running is the responsibility of the deployment tool.

Developer impact
----------------

More internal communication in Cyborg

Implementation
==============

Assignee(s)
-----------


Primary assignee:
  jkilpatr

Other contributors:
  zhuli

Work Items
----------

N/A


Dependencies
============

N/A


Testing
=======

N/A


Documentation Impact
====================

N/A

References
==========

N/A


History
=======

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Queens
     - Introduced
