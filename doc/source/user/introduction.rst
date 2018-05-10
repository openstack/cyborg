Introduction
============

Background Story
----------------

OpenStack Acceleration  Discussion Started from Telco Requirements:

* High level requirements first drafted in the standard organization
  ETSI NFV ISG
* High level requirements transformed into detailed requirements in
  OPNFV DPACC project.
* New project called Nomad established to address the requirements.
* BoF discussions back in OpenStack Austin Summit.

Transition to Cyborg Project:

* From a long period of conversation and discussion within the
  OpenStack community, we found that the initial goal of Nomad project
  to address acceleration management in Telco is too limited. From
  design summit session in Barcelona Summit, we have developers from
  Scientific WG help us understanding the need for acceleration
  management in HPC cloud, and we also had a lot of discussion on the
  Public Cloud support of accelerated instances.

* We decide to formally establish a project that will work on the
  management framework for dedicated devices in OpenStack, and there
  comes the Cyborg Project.

Definition Breakdown
--------------------

**General Management Framework:**
* Resource Discovery
* Life Cycle Management


**Accelerators:**
* Software: dpdk/spdk, pmem, ...
* Hardware: FPGA, GPU, ARM SoC, NVMe SSD, CCIX based Caches, ...
