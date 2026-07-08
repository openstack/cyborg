=========================
Contributor Documentation
=========================

Contributing to Cyborg gives you the power to help add features, fix bugs,
enhance documentation, and increase testing. Contributions of any type are
valuable, and part of what keeps the project going. Here are a list of
resources to get your started.

Basic Information
=================

.. toctree::
   :maxdepth: 2

   contributing

Contributing
============

* :doc:`/contributor/devstack_setup`: DevStack setup guide for Cyborg
  development

* :doc:`/contributor/vm-setup`: Creating development VMs for testing

* :doc:`/contributor/nvme-driver`: Cyborg NVMe driver development environment

* :doc:`/contributor/tempest-testing`: Running Cyborg tempest plugin tests

* :doc:`/contributor/api-sample-testing`: Running functional API sample
  validation tests

* :doc:`/contributor/grenade-upgrade`: Upgrade testing using grenade

* :doc:`/user/using-cyborg`: Using Cyborg with instances

Reviewing
=========

* :doc:`/contributor/microversions`: How the API is (micro)versioned and what
  you need to do when adding an API exposed feature that needs a new
  microversion.

* :doc:`/contributor/releasenotes`: When we need a release note for a
  contribution.

* :doc:`/contributor/driver-development-guide`: Get your driver development
  guide to contribute

* :doc:`/contributor/release-guide`: Chronological guide for release liaisons

* :doc:`/contributor/pci-sim/index`: pci-sim fake SR-IOV kernel module for
  PCI passthrough testing without physical hardware

.. # NOTE: toctree needs to be placed at the end of the section to
   # keep the document structure in the PDF doc.
.. toctree::
   :hidden:

   microversions
   releasenotes
   devstack_setup
   vm-setup
   nvme-driver
   tempest-testing
   api-sample-testing
   grenade-upgrade
   driver-development-guide
   release-guide
   pci-sim/index
