==========================
Install Cyborg from Source
==========================

This section describes how to install and configure the Acceleration Service
for Ubuntu 18.04.1 LTS from source code.

.. include:: common_prerequisites.rst

Install and Configure
---------------------

#.  Create a folder which will hold all Cyborg components.

    .. code-block:: console

        mkdir ~/cyborg

    ..

#.  Clone the cyborg git repository to the management server.

    .. code-block:: console

        cd ~/cyborg
        git clone git://git.openstack.org/openstack/cyborg
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

#.  Edit ``cyborg.conf`` with your favorite editor. Below is an example
    which contains basic settings you likely need to configure.

    .. code-block:: ini

        [DEFAULT]
        transport_url = rabbit://%RABBITMQ_USER%:%RABBITMQ_PASSWORD%@%OPENSTACK_HOST_IP%:5672/
        use_syslog = False
        state_path = /var/lib/cyborg
        debug = True

        ...

        [database]
        connection = mysql+pymysql://%DATABASE_USER%:%DATABASE_PASSWORD%@%OPENSTACK_HOST_IP%/cyborg

        ...

        [service_catalog]
        cafile = /opt/stack/data/ca-bundle.pem
        project_domain_id = default
        user_domain_id = default
        project_name = service
        password = cyborg
        username = cyborg
        auth_url = http://%OPENSTACK_HOST_IP%/identity
        auth_type = password

        ...

        [placement]
        project_domain_name = Default
        project_name = service
        user_domain_name = Default
        password = password
        username = placement
        auth_url = http://%OPENSTACK_HOST_IP%/identity
        auth_type = password
        auth_section = keystone_authtoken

        ...

        [keystone_authtoken]
        memcached_servers = localhost:11211
        signing_dir = /var/cache/cyborg/api
        cafile = /opt/stack/data/ca-bundle.pem
        project_domain_name = Default
        project_name = service
        user_domain_name = Default
        password = cyborg
        username = cyborg
        auth_url = http://%OPENSTACK_HOST_IP%/identity

    ..

#.  Install Cyborg packages.

    .. code-block:: console

        cd ~/cyborg/cyborg
        sudo python setup.py install
    ..

#.  Create database tables for Cyborg.

    .. code-block:: console

        cd /usr/local/bin
        cyborg-dbsync --config-file /etc/cyborg/cyborg.conf upgrade
    ..

#.  Install Cyborg API via WSGI :doc:`api-uwsgi <../admin/config-wsgi>`

.. note::

       Cyborg-api service can also be run as a Python command that
       runs a web serve, which can be launched as follows with different
       Acceleration service API endpoints as mentioned in Prerequisites part.
       However, we would like to recommend you the uwsgi way since when a
       project provides a WSGI application the API service gains
       flexibility in terms of deployment, performance, configuration
       and scaling. BYW, if you choose devstack to deploy your acceleration
       service, uwsgi is a default choice.

       cyborg-api --config-file=/etc/cyborg/cyborg.conf

#.  Launch Cyborg Conductor, Cyborg Agent services. Open a separate
    terminal for each service since the console will be locked by
    a running process.

    .. code-block:: console

        cyborg-conductor --config-file=/etc/cyborg/cyborg.conf
        cyborg-agent --config-file=/etc/cyborg/cyborg.conf
    ..
