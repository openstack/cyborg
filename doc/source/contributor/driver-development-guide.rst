:title: Driver Development Guide

Driver Development Guide
########################

The goal of this document is to explain how to develop a new kind of Cyborg
accelerator driver.

.. note::

  Make sure you have installed Openstack environment using devstack_ before development.

.. _devstack: https://docs.openstack.org/cyborg/latest/contributor/devstack_setup.html

Derive a new driver class
=========================

Imply the necessary interface, the list of interfaces is as follows:

.. code-block:: python

  class NewCyborgDriver(object):
      """Cyborg new accelerator driver.
      """

      def discover(self):
          """Discover specific accelerator
          :return: list of cyborg.objects.driver_objects.driver_device.
                   DriverDevice
          """
          pass

Modify setup.cfg
================

Add the new driver map into file ``cyborg/setup.cfg``:

.. code-block:: cfg

 [entry_points]
 cyborg.accelerator.driver =
     intel_fpga_driver = cyborg.accelerator.drivers.fpga.intel.driver:IntelFPGADriver
     new_driver_name = cyborg.accelerator.drivers.example.driver:NewCyborgDriver

Reinstall and Test
==================

Reinstall cyborg:

.. code-block:: console

 $ python setup.py develop

Restart cyborg-agent:

.. code-block:: console

 $ sudo systemctl restart devstack@cyborg-agent
