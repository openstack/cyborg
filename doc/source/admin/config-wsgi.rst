==============================
Installing Cyborg API via WSGI
==============================

The Cyborg API is provided as a WSGI application and must be hosted by a
standard WSGI server. This document describes how to deploy it using uWSGI.
DevStack also uses uWSGI for development.

WSGI Application
----------------

The function ``cyborg.api.wsgi_app.init_application`` will setup a WSGI
application to run behind uwsgi.

Cyborg API behind uwsgi
-----------------------

Create a ``cyborg-api-uwsgi`` file with content below:

.. code-block:: ini

    [uwsgi]
    chmod-socket = 666
    socket = /var/run/uwsgi/cyborg-wsgi-api.socket
    lazy-apps = true
    add-header = Connection: close
    buffer-size = 65535
    hook-master-start = unix_signal:15 gracefully_kill_them_all
    thunder-lock = true
    plugins = python
    enable-threads = true
    worker-reload-mercy = 90
    exit-on-reload = false
    die-on-term = true
    master = true
    processes = 2
    module = cyborg.wsgi.api:application

.. end

Start cyborg-api:

.. code-block:: console

    # uwsgi --ini /etc/cyborg/cyborg-api-uwsgi.ini

.. end

This configuration listens on a Unix socket. Configure an HTTP frontend,
such as Apache or nginx, to proxy requests to that socket. The mod_wsgi
configuration below is an alternative that hosts the application directly.

Cyborg API behind Apache mod_wsgi
---------------------------------

Unlike uWSGI, mod_wsgi does not support the ``module =
cyborg.wsgi.api:application`` syntax. Instead, configure
``WSGIScriptAlias`` with the path to the installed ``cyborg/wsgi/api.py``
file. That module exports the WSGI ``application`` object.

For example, the following configuration mounts the API at
``/accelerator``:

.. code-block:: apache

    <VirtualHost *:80>
        ServerName cyborg.example.com

        ErrorLog /var/log/apache2/cyborg-api-error.log
        CustomLog /var/log/apache2/cyborg-api-access.log combined

        WSGIApplicationGroup %{GLOBAL}
        WSGIDaemonProcess cyborg-api user=cyborg group=cyborg \
            processes=2 threads=1
        WSGIProcessGroup cyborg-api
        WSGIScriptAlias /accelerator \
            /usr/lib/python3/dist-packages/cyborg/wsgi/api.py

        <Directory /usr/lib/python3/dist-packages/cyborg/wsgi>
            Require all granted
        </Directory>
    </VirtualHost>

The Python module path varies by installation. For example, RPM-based
systems and virtual environments commonly install it below a
``site-packages`` directory rather than the ``dist-packages`` path shown
above. Replace the path in both directives with the path used by the Cyborg
installation. The mod_wsgi module must also be built for the same Python
runtime used to install Cyborg.
