Cyborg architecture
====================

Cyborg design can be described by following diagram:

.. image:: ../figures/cyborg-architecture.png
    :width: 700 px
    :scale: 99 %
    :align: left

**cyborg-api** - cyborg-api is a cyborg service that provides **REST API**
interface for the Cyborg project. It supports POST/PUT/DELETE/GET operations
and interacts with cyborg-agent and cyborg-db via cyborg-conductor.

**cyborg-conductor** - cyborg-conductor is a cyborg service that coordinates
interaction, DB access between cyborg-api and cyborg-agent.

**cyborg-agent** - cyborg-agent is a cyborg service that is responsible for
interaction with accelerator backends via the Cyborg Driver. For now the only
implementation in play is the Cyborg generic Driver. It will also handle the
communication with the Nova placement service. Cyborg-Agent will also write to
a local cache for local accelerator events.

**cyborg-generic-driver** - cyborg-generic-driver is a general multipurpose
driver with the common set of capabilities that any accelerators will have.
