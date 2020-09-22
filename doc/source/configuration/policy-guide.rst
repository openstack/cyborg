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

.. only:: html

   * :doc:`Sample Policy File <sample-policy>`: A sample cyborg
     policy file with inline documentation.

.. # NOTE(mriedem): This is the section where we hide things that we don't
   # actually want in the table of contents but sphinx build would fail if
   # they aren't in the toctree somewhere.
.. # NOTE(amotoki): toctree needs to be placed at the end of the secion to
   # keep the document structure in the PDF doc.
.. toctree::
   :hidden:

   policy

.. # NOTE(amotoki): Sample files are only available in HTML document.
   # Inline sample files with literalinclude hit LaTeX processing error
   # like TeX capacity exceeded and direct links are discouraged in PDF doc.
.. only:: html

   .. toctree::
      :hidden:

      sample-policy
