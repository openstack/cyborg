Common Configuration
--------------------

Regardless of the package or code source you must do the following
to properly setup the Accelerator Life Cycle Management service.
A database, service credentials, and API endpoints must be created.

#. To create the database, complete these steps:

   * Use the database access client to connect to the database
     server as the ``root`` user:

     .. code-block:: console

        $ mysql -u root -p
     ..

   * Create the ``cyborg`` database:

     .. code-block:: mysql

            CREATE DATABASE cyborg;
     ..

   * Grant proper access to the ``cyborg`` database:

     .. code-block:: mysql

            GRANT ALL PRIVILEGES ON cyborg.* TO 'cyborg'@'localhost' IDENTIFIED BY 'CYBORG_DBPASS';
     ..

     Replace ``CYBORG_DBPASS`` with a suitable password.

   * Exit the database access client.

     .. code-block:: mysql

            exit;
     ..

#. Source the ``admin`` credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc
   ..

#. To create the service credentials, complete these steps:

   * Create the ``cyborg`` user:

     .. code-block:: console

        $ openstack user create --domain default --password-prompt cyborg
     ..

   * Add the ``admin`` role to the ``cyborg`` user:

     .. code-block:: console

        $ openstack role add --project service --user cyborg admin
     ..

   * Create the cyborg service entities:

     .. code-block:: console

        $ openstack service create --name cyborg --description "Acceleration Service" accelerator
     ..

#. Create the Acceleration service API endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        accelerator public http://<cyborg-ip>/accelerator/v2
      $ openstack endpoint create --region RegionOne \
        accelerator internal http://<cyborg-ip>/accelerator/v2
      $ openstack endpoint create --region RegionOne \
        accelerator admin http://<cyborg-ip>/accelerator/v2
   ..

   .. note::

      URLs (publicurl, internalurl and adminurl) may be different
      depending on your environment.

   ..

Configure Cyborg
-----------------

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

        [nova]
        project_domain_name = Default
        project_name = service
        user_domain_name = Default
        password = password
        username = nova
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
        auth_type = password

    ..

#.  Create database tables for Cyborg.

    .. code-block:: console

        cyborg-dbsync --config-file /etc/cyborg/cyborg.conf upgrade
    ..

#.  Install Cyborg API via WSGI :doc:`api-uwsgi <../admin/config-wsgi>`.

#.  Launch Cyborg Conductor, Cyborg Agent services. Open a separate
    terminal for each service since the console will be locked by
    a running process.

    .. code-block:: console

        cyborg-conductor --config-file=/etc/cyborg/cyborg.conf
        cyborg-agent --config-file=/etc/cyborg/cyborg.conf
    ..
