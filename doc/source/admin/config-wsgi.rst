==============================
Installing Cyborg API via WSGI
==============================

Cyborg-api service can be run either as a Python command that runs a web serve
or As a WSGI application hosted by uwsgi. This document is a guide to deploy
cyborg-api using uwsgi. In devstack, uwsgi is used by default for development.

WSGI Application
----------------

The function ``cyborg.api.wsgi_app.init_application`` will setup a WSGI
application to run behind uwsgi.

Watcher API behind uwsgi
------------------------

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
    wsgi-file = /usr/local/bin/cyborg-wsgi-api

.. end

Start cyborg-api:

.. code-block:: console

    # uwsgi --ini /etc/cyborg/cyborg-api-uwsgi.ini

.. end
