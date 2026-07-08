==============================================
Running Functional API Sample Validation Tests
==============================================

Overview
========

Cyborg includes functional tests that validate API response structure
against the JSON sample files in ``doc/api_samples/``.  These tests
catch structural drift between the API and its documentation — missing
keys, extra keys, or type changes — without being sensitive to value
changes like UUIDs or timestamps.

Each test boots a real Pecan/WSME application against a file-backed
SQLite database, seeds test data, issues a GET request, and compares
the response *structure* (keys and value types) against the
corresponding sample file.

Running the Tests
=================

.. code-block:: console

   $ tox -efunctional

To run a single test class:

.. code-block:: console

   $ tox -efunctional -- cyborg.tests.functional.api.test_api_samples.TestDeviceSamples

How It Works
============

Structural comparison reduces each JSON document to a *type skeleton*:
dictionary keys are preserved, scalar values are replaced by their
Python type name (``str``, ``int``, ``bool``), and lists are
recursively reduced and sorted so element order does not matter.
``None``/``null`` values become ``mock.ANY`` so optional fields match
regardless of whether the sample or response carries a real value.

The test then uses ``assertEqual`` on the two skeletons.  If they
differ, the assertion error shows exactly which keys or types
diverged, along with the sample file path.

Regenerating Sample Files
=========================

When you intentionally change the API schema (adding a field, changing
a type), regenerate the sample files from actual API output:

.. code-block:: console

   $ GENERATE_SAMPLES=1 tox -efunctional

This overwrites the JSON files under ``doc/api_samples/`` with the
current API responses, formatted with ``sort_keys=True`` for stable
diffs.  Review the changes carefully before committing.

Adding a New Resource
=====================

1. Create a seed function in
   ``cyborg/tests/local_fixtures/common.py`` that inserts the
   necessary objects into the database and returns them in a dict.

2. Add a seed method to ``ApiSampleTestBase`` in
   ``cyborg/tests/functional/api/test_api_samples_base.py`` that
   calls the seed function and returns a dict of UUIDs.

3. Add a test class in
   ``cyborg/tests/functional/api/test_api_samples.py`` with test
   methods for the list and get-one endpoints.

4. Generate the initial sample files:

   .. code-block:: console

      $ GENERATE_SAMPLES=1 tox -efunctional

5. Review the generated sample files, then commit them along with the
   new test code.

Project Structure
=================

::

   cyborg/tests/
   ├── local_fixtures/          # Shared test fixtures
   │   ├── capture.py           # Logging and warnings fixtures
   │   ├── common.py            # Pecan app factory and seed functions
   │   ├── db_fixture.py        # File-backed SQLite DatabaseFixture
   │   ├── db_lock_fixture.py   # Write serialization for SQLite
   │   └── policy_fixture.py    # Policy override fixture
   └── functional/
       └── api/
           ├── test_api_samples.py       # Test classes per resource
           └── test_api_samples_base.py  # ApiSampleTestBase and helpers

   doc/api_samples/             # Reference JSON samples
   ├── accelerator_requests/
   ├── attributes/
   ├── deployables/
   ├── device_profiles/
   └── devices/
