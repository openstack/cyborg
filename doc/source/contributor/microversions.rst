API Microversions
=================

Background
----------

Cyborg uses a framework we call 'API Microversions' for allowing changes
to the API while preserving backward compatibility. The basic idea is
that a user has to explicitly ask for their request to be treated with
a particular version of the API. So breaking changes can be added to
the API without breaking users who don't specifically ask for it. This
is done with an HTTP header ``OpenStack-API-Version`` which has as its
value a string containing the name of the service, ``accelerator``, and
a monotonically increasing semantic version number starting from ``2.0``.
The full form of the header takes the form::

    OpenStack-API-Version: accelerator 2.0

If a user makes a request without specifying a version, they will get the
``_MIN_VERSION_STRING``(defined in ``cyborg/api/controllers/v2/versions.py``)
as the default version. This value is currently ``2.0`` and is expected to
remain so for quite a long time.

There is a special value ``latest`` which can be specified, which will
allow a client to always receive the most recent version
(``_MAX_VERSION_STRING`` defined in ``cyborg/api/controllers/v2/versions.py``)
of API responses from the server.

.. warning::

  The ``latest`` value is mostly meant for integration testing and
  would be dangerous to rely on in client code since Cyborg microversions
  are not following sever and therefore backward compatibility is not
  guaranteed. Clients, like python-cyborgclient, should always require a
  specific microversion but limit what is acceptable to the version range
  that it understands at the time.

For full details please read the `Ussuri spec for microversions
<https://specs.openstack.org/openstack/cyborg-specs/specs/ussuri/implemented/cyborg-api.html>`_
and `Microversion Specification
<http://specs.openstack.org/openstack/api-wg/guidelines/microversion_specification.html>`_.

When do I need a new Microversion?
----------------------------------

A microversion is needed when the contract to the user is
changed. The user contract covers many kinds of information such as:

- the Request

  - the list of resource urls which exist on the accelerator

    Example: adding a new accelerator_requests/{ID}/foo which didn't exist in a
    previous version of the code

  - the list of query parameters that are valid on urls

    Example: adding a new parameter ``is_yellow``
    accelerator_requests/{ID}?is_yellow=True

  - the list of query parameter values for non free form fields

    Example: parameter filter_by takes a small set of constants/enums "A",
    "B", "C". Adding support for new enum "D".

  - new headers accepted on a request

  - the list of attributes and data structures accepted.

    Example: adding a new attribute 'description' to the accelerator
    request body

- the Response

  - the list of attributes and data structures returned

    Example: adding a new attribute 'description' to the output
    of accelerator_requests/{ID}

  - the allowed values of non free form fields

    Example: adding a new allowed ``state`` to accelerator_requests/{ID}

  - the list of status codes allowed for a particular request

    Example: an API previously could return 200, 400, 403, 404 and the
    change would make the API now also be allowed to return 409.

    See [#f2]_ for the 400, 403, 404 and 415 cases.

  - new headers returned on a response.

  - changing a status code on a particular response.

    Example: changing the return code of an API from 501 to 400.

      .. note:: Fixing a bug so that a 400+ code is returned rather than a
          500 or 503 does not require a microversion change. It's assumed
          that clients are not expected to handle a 500 or 503 response and
          therefore should not need to opt-in to microversion changes that
          fixes a 500 or 503 response from happening.
          According to the OpenStack API Working Group, a **500 Internal
          Server Error** should **not** be returned to the user for failures
          due to user error that can be fixed by changing the request on the
          client side. See [#f1]_.

The following flow chart attempts to walk through the process of "do
we need a microversion".

.. graphviz::

   digraph states {

    label="Do I need a microversion?"

    silent_fail[shape="diamond", style="", group=g1, label="Did we silently
    fail to do what is asked?"];
    ret_500[shape="diamond", style="", group=g1, label="Did we return a 500
    before?"];
    new_error[shape="diamond", style="", group=g1, label="Are we changing what
    status code is returned?"];
    new_attr[shape="diamond", style="", group=g1, label="Did we add or remove
    an attribute to a payload?"];
    new_param[shape="diamond", style="", group=g1, label="Did we add or remove
    an accepted query string parameter or value?"];
    new_resource[shape="diamond", style="", group=g1, label="Did we add or
    remove a resource url?"];


   no[shape="box", style=rounded, label="No microversion needed"];
   yes[shape="box", style=rounded, label="Yes, you need a microversion"];
   no2[shape="box", style=rounded, label="No microversion needed, it's
   a bug"];

   silent_fail -> ret_500[label=" no"];
   silent_fail -> no2[label="yes"];

    ret_500 -> no2[label="yes [1]"];
    ret_500 -> new_error[label=" no"];

    new_error -> new_attr[label=" no"];
    new_error -> yes[label="yes"];

    new_attr -> new_param[label=" no"];
    new_attr -> yes[label="yes"];

    new_param -> new_resource[label=" no"];
    new_param -> yes[label="yes"];

    new_resource -> no[label=" no"];
    new_resource -> yes[label="yes"];

   {rank=same; yes new_attr}
   {rank=same; no2 ret_500}
   {rank=min; silent_fail}

   }


**Footnotes**

.. [#f1] When fixing 500 errors that previously caused stack traces, try
  to map the new error into the existing set of errors that API call
  could previously return (400 if nothing else is appropriate). Changing
  the set of allowed status codes from a request is changing the
  contract, and should be part of a microversion (except in [#f2]_).

  The reason why we are so strict on contract is that we'd like
  application writers to be able to know, for sure, what the contract is
  at every microversion in Cyborg. If they do not, they will need to write
  conditional code in their application to handle ambiguities.

  When in doubt, consider application authors. If it would work with no
  client side changes on both Cyborg versions, you probably don't need a
  microversion. If, on the other hand, there is any ambiguity, a
  microversion is probably needed.

.. [#f2] The exception to not needing a microversion when returning a
  previously unspecified error code is the 400, 403, 404 and 415 cases.
  This is considered OK to return even if previously unspecified in the
  code since it's implied given keystone authentication can fail with a
  403 and API validation can fail with a 400 for invalid json request body.
  Request to url/resource that does not exist always fails with 404.
  Invalid content types are handled before API methods are called which
  results in a 415.

    .. note:: When in doubt about whether or not a microversion is required
        for changing an error response code, consult the `Cyborg team`_.

.. _`Cyborg team`: https://review.opendev.org/#/admin/groups/1243,members


When a microversion is not needed
---------------------------------

A microversion is not needed in the following situation:

- the response

  - Changing the error message without changing the response code
    does not require a new microversion.

  - Removing an inapplicable HTTP header, for example, suppose the Retry-After
    HTTP header is being returned with a 4xx code. This header should only be
    returned with a 503 or 3xx response, so it may be removed without bumping
    the microversion.

  - An obvious regression bug in an admin-only API where the bug can still
    be fixed upstream on active stable branches. Admin-only APIs are less of
    a concern for interoperability and generally a regression in behavior can
    be dealt with as a bug fix when the documentation clearly shows the API
    behavior was unexpectedly regressed.

In Code
-------

In ``cyborg/api/controllers/v2/versions.py`` we define some constants below:

  - ``BASE_VERSION``: value is ``2`` which is intended to be used as the
    Cyborg API version.

  - ``MINOR_0_INITIAL_VERSION``: value is ``0`` to be used as the initial
    value of microversion.

  - ``MINOR_X_Y``: ``Y`` is the change you want to make, ``X`` is the min
    version to support ``Y``. For example, ``MINOR_1_PROJECT_ID`` means
    that the request ``project_id`` is supported from microversion ``2.1``.

  - ``MINOR_MAX_VERSION``: the max version, which equals to latest.

  - ``_MIN_VERSION_STRING``: the combination of ``BASE_VERSION`` and
    ``MINOR_0_INITIAL_VERSION``, which means the min version of Cyborg API.

  - ``_MAX_VERSION_STRING`` with the combination of ``BASE_VERSION`` and
    ``MINOR_MAX_VERSION``, which means the max version of Cyborg API.

In ``cyborg/api/controllers/v2/utils.py``, we define the check function of
microversion.

    For the example of `allow_project_id()` function, we compare the request
    version and the defined ``MINOR_1_PROJECT_ID`` to check whether the
    request is allowed. If the user's request with the version which is lower
    than ``MINOR_1_PROJECT_ID``, we will raise "Request not acceptable."
    exception to the user.

.. code:: python

    def allow_project_id():
        # v2.1 added project_id for arq patch
        return api.request.version.minor >= versions.MINOR_1_PROJECT_ID

Adding a new API method
~~~~~~~~~~~~~~~~~~~~~~~

In the controller class:

.. code:: python

    def my_api_method(self, req, id):
        if not utils.allow_project_id():
            raise exception.NotAcceptable(_(
                "Request not acceptable. The minimal required API "
                "version should be %(base)s.%(opr)s") %
                {'base': versions.BASE_VERSION,
                'opr': versions.MINOR_1_PROJECT_ID})

This method would only be available if the caller had specified an
``OpenStack-API-Version`` of >= ``accelerator 2.1``. If they had specified a
lower version (or not specified it and received the default of
``accelerator 2.0``) the server would respond with ``HTTP/406``.

Other necessary changes
-----------------------

If you are adding a patch which adds a new microversion, it is
necessary to add changes to other places which describe your change:

* Define ``MINOR_*{int}_**`` in
  ``cyborg/api/controllers/v2/versions.py``

* Update ``MINOR_MAX_VERSION`` to the defined ``MINOR_*{int}_**`` in
  ``cyborg/api/controllers/v2/versions.py``

* Add a verbose description of what changed in the new version to
  ``cyborg/api/rest_api_version_history.rst``.

* Add a :doc:`release note <releasenotes>` with a ``features``
  section announcing the new or changed feature and the microversion.

* Update the expected versions in affected tests, for example in
  ``cyborg.tests.unit.api.controllers.v2.test_arqs.TestARQsController#test_apply_patch_allow_project_id``.

* Make a new commit to python-cyborgclient and update corresponding
  files to enable the newly added microversion API.

* Update the `API Reference`_ documentation as appropriate. The source
  is located under `api-ref/source/`.

.. _`API Reference`: https://docs.openstack.org/api-ref/accelerator/v2/index.html

If applicable, add functional sample tests under
``cyborg_tempest_plugin/tests/api/``

Allocating a microversion
-------------------------

If you are adding a patch which adds a new microversion, it is
necessary to allocate the next microversion number. The minor number
of ``_MAX_API_VERSION`` will be incremented. This will also be the new
microversion number for the API change. Developers may need over time
to rebase their patch calculating a new version number as above based
on the updated value of ``_MAX_API_VERSION``.

Testing Microversioned API Methods
----------------------------------

Testing a microversioned API method is very similar to a normal controller
method test, you just need to add the ``OpenStack-API-Version``
header, for example:

.. code:: python

    req = fakes.HTTPRequest.blank('/testable/url/endpoint')
    req.headers = {'OpenStack-API-Version': 'accelerator 2.1'}
    req.api_version_request = api_version.APIVersionRequest('2.1')

    controller = controller.TestableController()

    res = controller.index(req)
    ... assertions about the response ...

For many examples of testing, the canonical examples are in
``cyborg.tests.unit.api.controllers.v2.test_arqs.TestARQsController#test_apply_patch_allow_project_id``.
