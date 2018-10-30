=============
Prerequisites
=============

Before you install and configure the Accelerator Life Cycle Management service,
you must create a database, service credentials, and API endpoints.

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

   * If cyborg-api service is deployed using uwsgi, create the following
     endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        accelerator public http://<cyborg-ip>/accelerator/v1
      $ openstack endpoint create --region RegionOne \
        accelerator internal http://<cyborg-ip>/accelerator/v1
      $ openstack endpoint create --region RegionOne \
        accelerator admin http://<cyborg-ip>/accelerator/v1
   ..

   * Otherwise, if cyborg-api service is running as a python process, create
     the following endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        accelerator public http://<cyborg-ip>:6666/v1
      $ openstack endpoint create --region RegionOne \
        accelerator internal http://<cyborg-ip>:6666/v1
      $ openstack endpoint create --region RegionOne \
        accelerator admin http://<cyborg-ip>:6666/v1
   ..

   .. note::

      URLs (publicurl, internalurl and adminurl) may be different
      depending on your environment.

   ..
