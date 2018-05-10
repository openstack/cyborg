cyborg Style Commandments
===============================================

If you haven't already done so read the OpenStack Style Commandments https://docs.openstack.org/hacking/latest/

Before you commit your code run tox against your patch using the command.

    tox .

If any of the tests fail correct the error and try again. If your code is valid
Python but not valid pep8 you may find autopep8 from pip useful.

Once you submit a patch integration tests will run and those may fail,
-1'ing your patch you can make a gerrit comment 'recheck ci' if you have
reviewed the logs from the jobs by clicking on the job name in gerrit and
concluded that the failure was spurious or otherwise not related to your patch.
If problems persist contact people on #openstack-cyborg or #openstack-infra.
