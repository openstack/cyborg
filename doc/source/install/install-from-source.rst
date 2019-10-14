==========================
Install Cyborg from Source
==========================

This section describes how to install and configure the Acceleration Service
for Ubuntu 18.04.1 LTS from source code.

Install from git repository
----------------------------

#.  Create a folder which will hold all Cyborg components.

    .. code-block:: console

        mkdir ~/cyborg

    ..

#.  Clone the cyborg git repository to the management server.

    .. code-block:: console

        cd ~/cyborg
        git clone https://opendev.org/openstack/cyborg
    ..

#.  Set up the cyborg config file

    First, generate a sample configuration file, using tox

    .. code-block:: console

        cd ~/cyborg/cyborg
        tox -e genconfig
    ..

    And make a copy of it for further modifications

    .. code-block:: console

        cp -r ~/cyborg/cyborg/etc/cyborg /etc
        cd /etc/cyborg
        ln -s cyborg.conf.sample cyborg.conf
    ..

#.  Install Cyborg packages.

    .. code-block:: console

        cd ~/cyborg/cyborg
        sudo python setup.py install
    ..

.. include:: common.rst
