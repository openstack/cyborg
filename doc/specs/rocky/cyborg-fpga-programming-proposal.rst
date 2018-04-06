..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

====================================================
        Cyborg FPGA Programming Service Proposal
====================================================

Blueprint url is not available yet
https://blueprints.launchpad.net/openstack-cyborg/+spec/cyborg-fpga-programming-ability

This spec proposes a Programming Service to be added to Cyborg to allow user
dynamically change the functions loaded on FPGA in cloud environment

Problem description
===================

A field-programmable gate array (FPGA) is an integrated circuit designed to be
configured by a customer or a designer after manufacturing. Their advantage
lies in that they are sometimes significantly faster for some applications
because of their parallel nature and optimality in terms of the number of
gates used for a certain process. In addition, FPGA can be reprogrammed based
on different applications Hence, using FPGA for application acceleration in
cloud has been becoming desirable. Cyborg as a management framwork for
heterogeneous accelerators, tracking, deploying and reprogramming FPGAs are
much needed features. Since the FPGA modelling has already been proposed in
another document, this spec will be focused on proposing Reporgramming
Service for FPGAs in Cyborg

Use Cases
---------

In the scenario of OpenCL, user loads the accelerators on FPGA for their
application. When different applications are executing on OpenCL environment,
the accelerators will be changed from time to time. It will not be feasible
to login to each host and change the FPGA configuration manually by lab admin.
Instead, through the reprogramming service, users can manage the functions
of FPGA using a set of REST APIs.

Similarly, during the maintenance of FPGA, admin needs to update/migrate
shells and bitstreams on FPGAs within data center. Cyborg Reprogramming
Service will allow them to use the APIs from a centralized console.

Since this is a pure proposal for programming APIs, it would not focus on
what the upstream use case/runtime is. Those details will be in separate
specs when needed.

Proposed change
===============
First of all, Cyborg needs to add extra REST APIs to allow others to invoke
the programming service. The REST api should have following format::

    Url: {base_url}/fpga/{deployable_uuid}
    Method: POST
    URL Params:
        None

    Data Params:
        glance_bitstream_uuid

    Success Response:
        POST:
            Code: 200
            Body: { "msg" : "bitstream has been loaded successfully"}

    Error Response
        Code: 401 UNAUTHORIZED
        Body: { error : "Log in" }
        OR
        Code: 422 Unprocessable Entry
        Body: { error : "User is not authorized to use the resource" }

    Sample Call:
        To program fpga resource with deployable_uuid=2864a139-c2cd-4f9f-abf3-44eb3f09b83c
        with bitstream with uuid=0b955a5b-f5dd-49d0-8c4f-28729427d303
        $.ajax({
          url: "/fpga/2864a139-c2cd-4f9f-abf3-44eb3f09b83c",
          data: {
            "glance_bitstream_uuid": "0b955a5b-f5dd-49d0-8c4f-28729427d303"
          },
          dataType: "json",
          type : "post",
          success : function(r) {
            console.log(r);
          }
        });

Second, implement the service in Cyborg which does three tasks: 1. identify
the host location of the requested FPGA/Partial Reconfiguraion(PR) Region(e.g.
on which host is the board located). 2. Check if the user(API caller,
OpenStack Login User, etc) has the privilige to use the given bitstream,
FPGA, or host. 3. If the previous checks pass, Cyborg will send the program
notification to the target host with requested FPGA.

Third, implement notification callee in Cyborg Agent. This should be a rpc
call with following signature::

    int program_fpga_with_bitstream(deployable_uuid, bitstream_uuid)

The function takes both deployable_uuid and bitstream_uuid as input. It uses
deployable_uuid to identify which specific FPGA/PR region is going to be
programmed and uses bitstream_uuid to retrieve bitstream from the bitstream
storage service (Glance in the context of OpenStack). In addition, this is a
synchronous meaning it will wait for the programming task to be completed and
then return a status code as integer. The return code should have following
interpretation:

+------+--------------------------------------------------------+
| code | meaning                                                |
+------+--------------------------------------------------------+
| 0    | program successfully                                   |
+------+--------------------------------------------------------+
| 1    | failed with unkown errors                              |
+------+--------------------------------------------------------+
| 2    | invalid deployable_uuid(target fpga not found)         |
+------+--------------------------------------------------------+
| 3    | invalid bitstream_uuid(bitstream can not be downloaded)|
+------+--------------------------------------------------------+

Alternatives
------------



Data model impact
-----------------


REST API impact
---------------
A rest api will be added to the Cyborg service as we discussed previously.
It should not impact any of the existing rest apis

Security impact
---------------
The access to FPGA/PR region and bitstreams should be carefully checked.

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
On the Cyborg Agent side, it relies on program() api implemented by vendor.


Implementation
==============

Assignee(s)
-----------
Primary assignee:
  Li Liu <liliu1@huawei.com>

Work Items
----------
* Implement the cyborg program service rest api
* Implement the cyborg program service
* Implement the notification call in Cyborg Agent, which invokes vendor driver


Dependencies
============

Testing
=======

Documentation Impact
====================
The Cyborg-Nova interaction related specs need to be aware the change of the
accelerators when FPGAs are being reprogrammed.

References
==========
None

History
=======

.. list-table:: Revisions
   :header-rows: 1

   * - Release Name
     - Description
   * - Rocky
     - Introduced
