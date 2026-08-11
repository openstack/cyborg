=================================
Cyborg Policy Configuration Guide
=================================

Cyborg, like most OpenStack projects, uses a policy language to restrict
permissions on REST API actions.

* :doc:`Policy Concepts <policy-concepts>`: In the Victoria
  release, Cyborg API policy defines new default roles with system scope
  capabilities. These new changes improve the security level and
  manageability of Cyborg API as they are richer in terms of handling
  access at system and project level token with 'Read' and 'Write' roles.

.. toctree::
   :hidden:

   policy-concepts

* :doc:`Policy Reference <policy>`: A complete reference of all
  policy points in cyborg and what they impact.

.. # NOTE(amotoki): toctree needs to be placed at the end of the section to
   # keep the document structure in the PDF doc.
.. toctree::
   :hidden:

   policy
