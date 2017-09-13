============
Contributing
============

Contributions are most welcome!  You must first create a
Launchpad account and `follow the instructions here <https://docs.openstack.org/infra/manual/developers.html#account-setup>`_
to get started as a new OpenStack contributor.

Once you've signed the contributor license agreement and read through
the above documentation, add your public SSH key under the 'SSH Public Keys'
section of review.openstack.org_.

.. _review.openstack.org: https://review.openstack.org/#/settings/

You can view your public key using:

::

    $ cat ~/.ssh/id_*.pub

Set your username and email for review.openstack.org:

::

    $ git config --global user.email "example@example.com"
    $ git config --global user.name "example"
    $ git config --global --add gitreview.username "example"

Next, Clone the github repository:

::

    $ git clone https://github.com/openstack/cyborg.git

You need to have git-review in order to be able to submit patches using
the gerrit code review system. You can install it using:

::

    $ sudo yum install git-review

To set up your cloned repository to work with OpenStack Gerrit

::

    $ git review -s

It's useful to create a branch to do your work, name it something
related to the change you'd like to introduce.

::

    $ cd cyborg
    $ git branch my_special_enhancement
    $ git checkout !$

Make your changes and then commit them using the instructions
below.

::

    $ git add /path/to/files/changed
    $ git commit

Use a descriptive commit title followed by an empty space.
You should type a small justification of what you are
changing and why.

Now you're ready to submit your changes for review:

::

    $ git review


If you want to make another patchset from the same commit you can
use the amend feature after further modification and saving.

::

    $ git add /path/to/files/changed
    $ git commit --amend
    $ git review

If you want to submit a new patchset from a different location
(perhaps on a different machine or computer for example) you can
clone the Cyborg repo again (if it doesn't already exist) and then
use git review against your unique Change-ID:

::

    $ git review -d Change-Id

Change-Id is the change id number as seen in Gerrit and will be
generated after your first successful submission.

The above command downloads your patch onto a separate branch. You might
need to rebase your local branch with remote master before running it to
avoid merge conflicts when you resubmit the edited patch.  To avoid this
go back to a "safe" commit using:

::

    $ git reset --hard commit-number

Then,

::

    $ git fetch origin

::

    $ git rebase origin/master

Make the changes on the branch that was setup by using the git review -d
(the name of the branch is along the lines of
review/username/branch_name/patchsetnumber).

Add the files to git and commit your changes using,

::

    $ git commit --amend

You can edit your commit message as well in the prompt shown upon
executing above command.

Finally, push the patch for review using,

::

    $ git review

Adding functionality
--------------------

If you are adding new functionality to Cyborg please add testing for that functionality
and provide a detailed commit message outlining the goals of your commit and how you
achived them.

If the functionality you wish to add doesn't fix in an existing part of the Cyborg
achitecture diagram drop by our team meetings to disscuss how it could be implemented

