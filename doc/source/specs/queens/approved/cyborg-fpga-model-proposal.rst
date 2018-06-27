..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
        Cyborg FPGA Model Proposal
==========================================

Blueprint url is not available yet
https://blueprints.launchpad.net/openstack-cyborg/+spec/cyborg-fpga-modelling

This spec proposes the DB modelling schema for tracking reprogrammable
resources

Problem description
===================

A field-programmable gate array (FPGA) is an integrated circuit designed to be
configured by a customer or a designer after manufacturing. Their advantage
lies in that they are sometimes significantly faster for some applications
because of their parallel nature and optimality in terms of the number of gates
used for a certain process. Hence, using FPGA for application acceleration in
cloud has been becoming desirable. Cyborg as a management framwork for
heterogeneous accelerators, tracking and deploying FPGAs are much needed
features.


Use Cases
---------

When user requests FPGA resources, scheduler will use placement agent [1]_ to
select appropriate hosts that have the requested FPGA resources.

When a FPGA type resource is allocated to a VM, Cyborg needs to track down
which exact device has been assigned in the database. On the other hand, when
the resource is released, Cyborg will need to be detached and free the exact
resource.

When a new device is plugged in to the system(host), Cyborg needs to discover
it and store it into the database

Proposed change
===============

We need to add 2 more tables to Cyborg database, one for tracking all the
deployables and one for arbitrary key-value pairs of deplyable associated
attirbutes. These tables are named as Deployables and Attributes.

Deployables table consists of all the common attributes columns as well as
a parent_id and a root_id. The parent_id will point to the associated parent
deployable and the root_id will point to the associated root deployable.
By doing this, we can form a nested tree structure to represent different
hierarchies. In addition, there will a foreign key named accelerator_id
reference to the accelerators table. For the case where FPGA has not been
loaded any bitstreams on it, they will still be tracked as a Deployable but
no other Deployables referencing to it. For instance, a network of
FPGA hierarchies can be formed using deployables in following scheme::

                            -------------------
        ------------------->|Deployable - FPGA|<--------------------
        |                   -------------------                    |
        |                           /\                             |
        | root_id                  /  \  parent_id/root_id         |
        |                         /    \                           |
        |         -----------------    -----------------           |
        |         |Deployable - PF|    |Deployable - PF|           |
        |         -----------------    -----------------           |
        |               /\                                         |
        |              /  \  parent_id                     root_id |
        |             /    \                                       |
    -----------------      -----------------                       |
    |Deployable - VF|      |Deployable - VF| -----------------------
    -----------------      -----------------


Attributes table consists of a key and a value columns to represent arbitrary
k-v pairs.

For instance, bitstream_id and function kpi can be tracked in this table.
In addition, a foreign key deployable_id refers to the Deployables table and
a parent_attribute_id to form nested structured attribute relationships.

Cyborg needs to have object classes to represent different types of
deployables(e.g. FPGA, Physical Functions, Virtual Functions etc).

Cyborg Agent needs to add feature to discover the FPGA resources from FPGA
driver and report them to the Cyborg DB through the conductor.

Conductor needs to add couple of sets of APIs for different types of deployable
resources.

Alternatives
------------

Alternativly, instead of having a flat table to track arbitrary hierarchies, we
can use two different tables in Cyborg database, one for physical functions and
one for virtual functions. physical_functions should have a foreign key
constraint to reference the id in Accelerators table. In addition,
virtual_functions should have a foreign key constraint to reference the id
in physical_functions.

The problems with this design are as follows. First, it can only track up to
3 hierarchies of resources. In case we need to add another layer, a lot of
migaration work will be required. Second, even if we only need to add some new
attribute to the existing resource type, we need to create new migration
scripts for them. Overall the maintenance work is tedious.

Data model impact
-----------------
As discussed in previous sections, two tables will be added: Deployables and
Attributes::


    CREATE TABLE Deployables
      (
        id           INTEGER NOT NULL ,     /*Primary Key*/
        parent_id    INTEGER ,              /*Pointer to the parent deployable's primary key*/
        root_id      INTEGER ,              /*Pointer to the root deployable's primary key*/
        name         VARCHAR2 (32 BYTE) ,   /*Name of the deployable*/
        pcie_address VARCHAR2 (32 BYTE) ,   /*pcie address which can be used for passthrough*/
        uuid         VARCHAR2 (32 BYTE) ,   /*uuid v4 format for the deployable itself*/
        node_id      VARCHAR2 (32 BYTE) ,   /*uuid v4 format to identify which host this deployable is located*/
        board        VARCHAR2 (16 BYTE) ,   /*Identify the model of the deployable(e.g. KU115)*/
        vendor       VARCHAR2 (16 BYTE) ,   /*Identify the vendor of the deployable(e.g. Xilinx)*/
        version      VARCHAR2 (32 BYTE) ,   /*Identify the version of the deployable(e.g. 1.2a)*/
        type         VARCHAR2 (32) ,        /*Identify the type of the deployable(e.g. FPGA/PF/VF)*/
        assignable   CHAR (1) ,             /*Represent if the deployable can be assigned to users*/
        instance_id  VARCHAR2 (32 BYTE) ,   /*Represent which instance this deployable has been assigned to*/
        availability INTEGER NOT NULL,      /*enum type to represent the status of the deployable(e.g. acclocated/claimed)*/
        accelerator_id INTEGER NOT NULL     /*foreign key references to the accelerator table*/
      ) ;
    ALTER TABLE Deployables ADD CONSTRAINT Deployables_PK PRIMARY KEY ( id ) ;
    ALTER TABLE Deployables ADD CONSTRAINT Deployables_accelerators_FK FOREIGN KEY ( accelerator_id ) REFERENCES accelerators ( id ) ;


    CREATE TABLE Attributes
      (
        id            INTEGER NOT NULL ,    /*Primary Key*/
        deployable_id INTEGER NOT NULL ,    /*foreign key references to the Deployables table*/
        KEY CLOB ,                          /*Attribute Key*/
        value CLOB ,                        /*Attribute Value*/
        parent_attribute_id INTEGER         /*Pointer to the parent attribute's primary key*/
      ) ;
    ALTER TABLE Attributes ADD CONSTRAINT Attributes_PK PRIMARY KEY ( id ) ;
    ALTER TABLE Attributes ADD CONSTRAINT Attributes_Deployables_FK FOREIGN KEY ( deployable_id ) REFERENCES Deployables ( id ) ON
    DELETE CASCADE ;


RPC API impact
---------------
Two sets of conductor APIs need to be added. 1 set for physical functions,
1 set for virtual functions

Physical function apis::

    def physical_function_create(context, values)
    def physical_function_get_all_by_filters(context, filters, sort_key='created_at', sort_dir='desc', limit=None, marker=None, columns_to_join=None)
    def physical_function_update(context, uuid, values, expected=None)
    def physical_function_destroy(context, uuid)

Virtual function apis::

    def virtual_function_create(context, values)
    def virtual_function_get_all_by_filters(context, filters, sort_key='created_at', sort_dir='desc', limit=None, marker=None, columns_to_join=None)
    def virtual_function_update(context, uuid, values, expected=None)
    def virtual_function_destroy(context, uuid)

REST API impact
---------------
Since these tables are not exposed to users for modifying/adding/deleting,
Cyborg will only add two extra REST APIs to allow user query information
related to deployables and their attributes.

API for retrieving Deployable's information::

    Url: {base_url}/accelerators/deployable/{uuid}
    Method: GET
    URL Params:
        GET: uuid --> get deplyable by uuid

    Data Params:
        None

    Success Response:
        GET:
            Code: 200
            Content: { deployable: {id : 12, parent_id: 11, root_id: 10, ....}}

    Error Response
        Code: 401 UNAUTHORIZED
        Content: { error : "Log in" }
        OR
        Code: 422 Unprocessable Entry
        Content: { error : "deployable uuid invalid" }

    Sample Call:
        To get the deployable with uuid=2864a139-c2cd-4f9f-abf3-44eb3f09b83c
        $.ajax({
          url: "/accelerators/deployable/2864a139-c2cd-4f9f-abf3-44eb3f09b83c",
          dataType: "json",
          type : "get",
          success : function(r) {
            console.log(r);
          }
        });

API for retrieving list of Deployables with filters/attirbutes::

    Url: {base_url}/accelerators/deployable
    Method: GET
    URL Params:
        None

    Data Params:
        k-v pairs for filtering

    Success Response:
        GET:
            Code: 200
            Content: { deployables: [{id : 12, parent_id: 11, root_id: 10, ....}]}

    Error Response
        Code: 401 UNAUTHORIZED
        Content: { error : "Log in" }
        OR
        Code: 422 Unprocessable Entry
        Content: { error : "deployable uuid invalid" }

    Sample Call:
        To get a list of FPGAs with no bitstream loaded.
        $.ajax({
          url: "/accelerators/deployable",
          data: {
            "bitstream_id": None,
            "type": "FPGA"
          },
          dataType: "json",
          type : "get",
          success : function(r) {
            console.log(r);
          }
        });

API for retrieving Deployable attributes' information::

    Url: {base_url}/accelerators/deployable/{uuid}/attribute/{key}
    Method: GET
    URL Params:
        GET: uuid --> uuid for the associated deployable
             key  --> key for the associated deployable

    Data Params:
        None

    Success Response:
        GET:
            Code: 200
            Content: { attribute: {key : value}}

    Error Response
        Code: 401 UNAUTHORIZED
        Content: { error : "Log in" }
        OR
        Code: 422 Unprocessable Entry
        Content: { error : "attirbute key invalid" }

    Sample Call:
        To get the value of key=kpi for deployable with id=2864a139-c2cd-4f9f-abf3-44eb3f09b83c
        $.ajax({
          url: "/accelerators/deployable/2864a139-c2cd-4f9f-abf3-44eb3f09b83c/attribute/kpi",
          dataType: "json",
          type : "get",
          success : function(r) {
            console.log(r);
          }
        });

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

There will be new functionalities available to the dev because of this work.


Implementation
==============

Assignee(s)
-----------
Primary assignee:
  Li Liu <liliu1@huawei.com>

Work Items
----------
* Create migration scripts to add two more tables to the database
* Create models in sqlalchemy as well as related conductor APIs
* Create corespoinding objects
* Create Conductor APIs to allow resourece reporting


Dependencies
============

Testing
=======
* Unit tests will be added test Cyborg generic driver.

Documentation Impact
====================
Document FPGA Modelling in the Cyborg project

References
==========
.. [1] https://docs.openstack.org/nova/latest/user/placement.html

History
=======

.. list-table:: Revisions
   :header-rows: 1

   * - Release
     - Description
   * - Queens
     - Introduced
