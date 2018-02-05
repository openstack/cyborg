Cyborg REST API v1.0
********************

General Information
===================

This document describes the basic REST API operation that Cyborg supports
for Pike release.

+--------+-----------------------+-------------------------------------------------------------------------------+
| Verb   | URI                   | Description                                                                   |
+========+=======================+===============================================================================+
| GET    | /accelerators         | Return a list of accelerators                                                 |
+--------+-----------------------+-------------------------------------------------------------------------------+
| GET    | /accelerators/{uuid}  | Retrieve a certain accelerator info identified by `{uuid}`                    |
+--------+-----------------------+-------------------------------------------------------------------------------+
| POST   | /accelerators         | Create a new accelerator.                                                     |
+--------+-----------------------+-------------------------------------------------------------------------------+
| PUT    | /accelerators/{uuid}  | Update the spec for the accelerator identified by `{uuid}`                    |
+--------+-----------------------+-------------------------------------------------------------------------------+
| DELETE | /accelerators/{uuid}  | Delete the accelerator identified by `{uuid}`                                 |
+--------+-----------------------+-------------------------------------------------------------------------------+

