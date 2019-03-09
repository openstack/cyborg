Cyborg REST API v1.0
********************

General Information
===================

This document describes the basic REST API operation that Cyborg supports
for Stein release::

    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | Verb   | URI                                     | Description                                                           |
    +========+=========================================+=======================================================================+
    | GET    | /accelerators                           | Return a list of accelerators (Deprecated)                             |
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | GET    | /accelerators/{uuid}                    | Retrieve a certain accelerator info identified by `{uuid}` (Deprecated)|
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | POST   | /accelerators                           | Create a new accelerator (Deprecated)                                  |
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | PUT    | /accelerators/{uuid}                    | Update the spec for the accelerator identified by `{uuid}` (Deprecated)|
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | DELETE | /accelerators/{uuid}                    | Delete the accelerator identified by `{uuid}` (Deprecated)             |
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | GET    | /accelerators/deployables/              | Return a list of deployables                                          |
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | GET    | /accelerators/deployables/{uuid}        | Retrieve a certain deployable info identified by `{uuid}`             |
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | POST   | /accelerators/deployables/              | Create a new deployable                                               |
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | PATCH  | /accelerators/deployables/{uuid}/program| Program a new deployable(FPGA)                                        |
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | PATCH  | /accelerators/deployables/{uuid}        | Update the spec for the deployable identified by `{uuid}`             |
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
    | DELETE | /accelerators/deployables/{uuid}        | Delete the deployable identified by `{uuid}`                          |
    +--------+-----------------------------------------+-----------------------------------------------------------------------+
