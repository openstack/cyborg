===============================
Using Cyborg with Your Instance
===============================

This guide shows you how to create OpenStack instances with accelerators
using Cyborg.

Prerequisites
=============

You need:

- Working Cyborg deployment
- OpenStack credentials
- Basic familiarity with OpenStack CLI

If you need to set up a development/testing environment from scratch:

- :doc:`/contributor/vm-setup` - Creating a development VM
- :doc:`/contributor/devstack_setup` - Installing DevStack with Cyborg
- :doc:`/contributor/nvme-driver` - Configuring NVMe devices (for NVMe testing)

Discovering Available Devices
==============================

List devices detected by Cyborg:

.. code-block:: console

   $ openstack accelerator device list
   +--------------------------------------+------+--------+-----------------+------------------------------------------------+
   | uuid                                 | type | vendor | hostname        | std_board_info                                 |
   +--------------------------------------+------+--------+-----------------+------------------------------------------------+
   | ece74dd7-c15f-4dca-b68f-f6fe189fcc1e | GPU  | 1af4   | cyborg-devstack | {"product_id": "1044", "controller": null}     |
   | 57763ef1-47cf-46b2-9d1d-047a16daf90b | FPGA | 0xABCD | cyborg-devstack | {"device_id": "0xabcd", "class": "Fake class"} |
   | 815146e7-48a3-4906-a0b5-47aee53abada | GPU  | 1b36   | cyborg-devstack | {"product_id": "0010", "controller": null}     |
   +--------------------------------------+------+--------+-----------------+------------------------------------------------+

List device attributes to find the trait you need:

.. code-block:: console

   $ openstack accelerator device attribute list
   +--------------------------------------+---------------+---------+----------------------------+
   | uuid                                 | deployable_id | key     | value                      |
   +--------------------------------------+---------------+---------+----------------------------+
   | ccc65d65-aa0e-48e1-af67-ac933e837124 |             1 | rc      | CUSTOM_PCI                 |
   | a226385b-546b-4113-ba11-d562fd440c7f |             1 | trait0  | CUSTOM_PCI_PRODUCT_ID_1044 |
   | 8fa79f37-040e-492d-a824-404f3f84e098 |             2 | traits1 | CUSTOM_FAKE_DEVICE         |
   | ae23a6f7-33c0-4a8f-86fa-d7e15aea26cc |             2 | rc      | FPGA                       |
   | ba104215-b713-42eb-ab90-663c7bb9a7c8 |             3 | rc      | CUSTOM_PCI                 |
   | 34347cc9-790b-4712-938d-a201ac557b5d |             3 | trait0  | CUSTOM_PCI_PRODUCT_ID_0010 |
   +--------------------------------------+---------------+---------+----------------------------+

Note the trait for the device you want to use (e.g.,
``CUSTOM_PCI_PRODUCT_ID_0010``).

Creating Device Profiles
=========================

Create a device profile using the trait from the previous step:

.. code-block:: console

   $ openstack accelerator device profile create nvme-profile \
       '[{"resources:CUSTOM_PCI": "1", "trait:CUSTOM_PCI_PRODUCT_ID_0010": "required"}]'

Verify the profile was created:

.. code-block:: console

   $ openstack accelerator device profile list
   +--------------------------------------+---------------------+---------------------------------------------------------------------------------+-------------+
   | uuid                                 | name                | groups                                                                          | description |
   +--------------------------------------+---------------------+---------------------------------------------------------------------------------+-------------+
   | 6a071e1d-d066-4b0e-850c-7b2adaf94ca6 | nvme-profile        | [{'resources:CUSTOM_PCI': '1', 'trait:CUSTOM_PCI_PRODUCT_ID_0010': 'required'}] | None        |
   +--------------------------------------+---------------------+---------------------------------------------------------------------------------+-------------+

Check: ``name`` column shows ``nvme-profile``.

Creating Flavors with Accelerators
===================================

Create a flavor:

.. code-block:: console

   $ openstack flavor create --ram 2048 --disk 20 --vcpus 2 accel-flavor

Link the device profile to the flavor:

.. code-block:: console

   $ openstack flavor set accel-flavor --property "accel:device_profile=nvme-profile"

Verify the flavor has the device profile:

.. code-block:: console

   $ openstack flavor show accel-flavor
   +----------------------------+---------------------------------------+
   | Field                      | Value                                 |
   +----------------------------+---------------------------------------+
   | OS-FLV-DISABLED:disabled   | False                                 |
   | OS-FLV-EXT-DATA:ephemeral  | 0                                     |
   | access_project_ids         | None                                  |
   | description                | None                                  |
   | disk                       | 20                                    |
   | id                         | 8607835f-9abc-4a3b-9bc5-bae54ff806e6  |
   | name                       | accel-flavor                          |
   | os-flavor-access:is_public | True                                  |
   | properties                 | accel:device_profile='nvme-profile'   |
   | ram                        | 2048                                  |
   | rxtx_factor                | 1.0                                   |
   | swap                       | 0                                     |
   | vcpus                      | 2                                     |
   +----------------------------+---------------------------------------+

Check: ``properties`` field shows ``accel:device_profile='nvme-profile'``.

Preparing Instance Prerequisites
=================================

Create SSH keypair (if you don't have one):

.. code-block:: console

   $ ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
   $ openstack keypair create --public-key ~/.ssh/id_ed25519.pub mykey

Or if you already have a key:

.. code-block:: console

   $ openstack keypair create --public-key ~/.ssh/id_ed25519.pub mykey

Download and upload a cloud image:

.. code-block:: console

   $ wget https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img
   $ openstack image create \
       --disk-format qcow2 \
       --container-format bare \
       --public \
       --file ubuntu-24.04-server-cloudimg-amd64.img \
       ubuntu-24.04

Creating Instances with Accelerators
=====================================

Create the instance using the flavor with the device profile:

.. code-block:: console

   $ openstack server create \
       --flavor accel-flavor \
       --image ubuntu-24.04 \
       --key-name mykey \
       --network private \
       test-instance

Check instance status:

.. code-block:: console

   $ openstack server list
   +--------------------------------------+--------------------+--------+---------------------------------------------------------+--------------+-------------+
   | ID                                   | Name               | Status | Networks                                                | Image        | Flavor      |
   +--------------------------------------+--------------------+--------+---------------------------------------------------------+--------------+-------------+
   | 06f3a96e-f064-4942-9a31-0904a7f2e106 | test-instance      | ACTIVE | private=10.0.0.15, fd01:4bf0:40e8:0:f816:3eff:fec8:78b7 | ubuntu-24.04 | accel-flavor |
   +--------------------------------------+--------------------+--------+---------------------------------------------------------+--------------+-------------+

Wait until ``Status`` column shows ``ACTIVE``.

Verifying Accelerator Attachment
=================================

Check Accelerator Request (ARQ) bindings:

.. code-block:: console

   $ openstack accelerator arq list
   +--------------------------------------+-------+---------------------+--------------------------------------+--------------------+--------------------------------------+
   | uuid                                 | state | device_profile_name | instance_uuid                        | attach_handle_type | attach_handle_info                   |
   +--------------------------------------+-------+---------------------+--------------------------------------+--------------------+--------------------------------------+
   | a73e2048-016d-49b3-a9fc-8f09e413f2bd | Bound | nvme-profile        | 06f3a96e-f064-4942-9a31-0904a7f2e106 | PCI                | {'bus': '00', 'device': '12',        |
   |                                      |       |                     |                                      |                    | 'domain': '0000', 'function': '0'}   |
   +--------------------------------------+-------+---------------------+--------------------------------------+--------------------+--------------------------------------+

Check: ``state`` column shows ``Bound`` = device successfully attached.

Deleting Instances
==================

Delete the instance:

.. code-block:: console

   $ openstack server delete test-instance

Verify instance is deleted:

.. code-block:: console

   $ openstack server list

Check ARQs are cleaned up:

.. code-block:: console

   $ openstack accelerator arq list

If ``state`` shows ``Deleting``, wait a moment and check again.

Empty list = cleanup complete, device available for reuse.
