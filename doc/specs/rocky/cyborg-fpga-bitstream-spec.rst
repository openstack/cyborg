..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/4.0/legalcode

====================================================
        Cyborg FPGA Bitstream metadata spec
====================================================

Blueprint url:
https://blueprints.launchpad.net/openstack-cyborg/+spec/cyborg-fpga-bitstream-metadata-spec

This spec proposes the FPGA Bitstream metadata specifications for bitstream
management

Problem description
===================

A field-programmable gate array (FPGA) is an integrated circuit designed to be
configured by a customer or a designer after manufacturing. Their advantage
lies in that they are sometimes significantly faster for some applications
because of their parallel nature and optimality in terms of the number of
gates used for a certain process. Hence, using FPGA for application
acceleration in cloud has become desirable. One of the encountered problems is
when it comes to bitstream management, it is difficult to map bitstreams to
their appropriate FPGA boards or reconfigurable regions. The aim of this
proposal is to provide a standardized set of metadata which should be
encapsulated together with bitstream storage.

Use Cases
---------

When user requests to reprogram a FPGA board with certain functionality in the
cloud environment, he or she will need to retrieve a suitable bitstream from
the storage. In order to find the suitable one, bitstreams need to be
categorized based on some properties defined in metadata.

Proposed change
===============

For each metadata, it will be stored as a row in this Glance's image_properties
in key-value pair format: column [name] holds the key whereas column [value]
holds the value. Note: no batabase schema change is required. This is a
standardization document to guide how to use existing Glance table for FPGA
bitstreams.

Given this, Cyborg will standardize the key convention as follows:

+--------------+---------+-----------+--------------------------------------+
| name         |  value  |  nullable | description                          |
+--------------+---------+-----------+--------------------------------------+
| bs-name      |  aes-128|  False    | name of the bitstream(not unique)    |
+--------------+---------+-----------+--------------------------------------+
| bs-uuid      |  {uuid} |  False    | The uuid generated during synthesis  |
+--------------+---------+-----------+--------------------------------------+
| vendor       |  Xilinx |  False    | Vendor of the card                   |
+--------------+---------+-----------+--------------------------------------+
| board        |  KU115  |  False    | Board type for this bitstream to load|
+--------------+---------+-----------+--------------------------------------+
| shell_id     |  {uuid} |  True     | Required shell bs-uuid for the bs    |
+--------------+---------+-----------+--------------------------------------+
| version      |  1.0    |  False    | Device version number                |
+--------------+---------+-----------+--------------------------------------+
| driver       |  SDX    |  True     | Type of driver for this bitstream    |
+--------------+---------+-----------+--------------------------------------+
| driver_ver   |  1.0    |  False    | Driver version                       |
+--------------+---------+-----------+--------------------------------------+
| driver_path  |  /path/ |  False    | Where to retrieve the driver binary  |
+--------------+---------+-----------+--------------------------------------+
| topology     |  {CLOB} |  False    | Function Topology                    |
+--------------+---------+-----------+--------------------------------------+
| description  |  desc   |  True     | Description                          |
+--------------+---------+-----------+--------------------------------------+
| region_uuid  |  {uuid} |  True     | The uuid for target region type      |
+--------------+---------+-----------+--------------------------------------+
| function_uuid|  {uuid} |  False    | The uuid for bs function type        |
+--------------+---------+-----------+--------------------------------------+
| function_name|  nic-40 |  True     | The function name for this bitstream |
+--------------+---------+-----------+--------------------------------------+

Here are the details regarding some definded keys.

[shell_id]
This field is optional. If a loading this PR bitstream requires a shell image,
this field specifies the shell bitstream's uuid. If it field is null, it means
this bitstream is a shell bitstream.

[driver]
This specifies the path to a package of scripts/binaries to be installed in
order to use the loaded bitstream(e.g. insmod some kernel driver/git clone
some remote source code, etc)

[region_uuid]
This value specifies the type of region that is required to load this
bitstream. This type is a uuid generated during the shell bitstream synthesis.

[function_uuid]
This value specifies the type of function for this bitstream. It helps the
upsteam scheduler to match traits with appropriate bitstream.

[topology]
This field describes the topology of function structures after the bitstream is
loaded on the FPGA. In particular, it uses JSON format to visualize how
physical functions, virtual functions are co-related to each other. It is
vendor driver's responsibility to interpret this and prepare the porper report
for Cyborg Agent. For instance::

    {
      "pf_num": 2,
      "vf_num": 2,
      "pf": [
        {
          "name": "pf_1",
          "capability": "",
          "kpi": "",
          "pci_offset": "0",
          "vf": [
            {
              "name": "vf_1",
              "pci_offset": "1"
            }
          ]
        },
        {
          "name": "pf_2",
          "capability": "",
          "kpi": "",
          "pci_offset": "2",
          "vf": [
            {
              "name": "vf_2",
              "pci_offset": "3"
            }
          ]
        }
      ]
    }

This JSON template guides Cyborg Agent to populate vf/pf/deployable list in
Cyborg.

Given the above JSON topology, Cyborg Driver should be able to interpret the
accelerator structure as follows::

                             =============
                             =Accelerator=
                             =============
                                   |
                             ============
                             =Deployable=
                             ============
                                  /\
                                 /  \
               ===================  ===================
               = Deployable pf_1 =  = Deployable pf_2 =
               ===================  ===================
                              |        |
                              |        |
               ===================  ===================
               = Deployable vf_1 =  = Deployable vf_2 =
               ===================  ===================

Noted: 1. Topology is not mandatory to fill in, as long as vendor driver can
figure out what resources to report after the bitstream is loaded. 2. The JSON
provided here is only a reference template. It does not have to be PCI-centric
etc. and up to vendors how to define it for their products. 3. A root
deployable shouldbe created in the graph. In addition, the pfs and vfs here
are all instances of deployable. Please refer to the DB objects specs
regarding physical_function and virtual_function.


Finnally, all of the FPGA bitstreams should be TAGGED as "FPGA" in Glance.
This helps distinguishing between normal VM images and bitstream images
during filtering.

Alternatives
------------


Data model impact
-----------------

RPC API impact
---------------

REST API impact
---------------

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
Accelerator vendors should implement the logic in program() api to populate
the loaded topology


Implementation
==============

Assignee(s)
-----------
Primary assignee:
  Li Liu <liliu1@huawei.com>
  Shaohe Feng <shaohe.feng@intel.com>

Work Items
----------
* Provide example JSON format for bitstream
* Provide example implementation of vendor driver

Dependencies
============

Testing
=======

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

   * - Release Name
     - Description
   * - Rocky
     - Introduced
