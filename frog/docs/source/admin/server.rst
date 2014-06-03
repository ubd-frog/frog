.. _server:

Server Setup
============

This page will guide you through setting up a production server for a proper deployment.  There are many giudes out the to get a full Python/Django stack going so this is not meant to be definitive.  The point here is to get a webserver running that can handle the traffic you require.  This guide assumes a server running Ubuntu 12.04, though as long as you can install or build the dependencies, and distro would work.  I haven't set up a production server using IIS, but I'm sure there are guides to getting python and Django running on it.


The Parts
---------

At the time of this writing, a common flavor is to use nginx and gunicorn.  Nginx will be your main server and will serve static content such as JavaScript and images, then pass on any requests to gunicorn that need to be handled by Django.  This makes for fast handling of the large images Frog is meant to display and a lightweight system to maintain down the road.  As for a database, I'll be using MySQL, but I believe Postgres, or any other DB supported by `Django's ORM <https://docs.djangoproject.com/en/1.5/ref/databases/>`_, would work as well.

- `nginx <http://wiki.nginx.org/Main>`_
- `gunicorn <http://gunicorn.org/>`_
- `MySQL <http://www.mysql.com/>`_


Install Packages
----------------

Since Ubuntu 12.04 comes with python 2.7, we'll just use that.  We will need to install PIP and distribute though.  I'll assume we'll be in `/var/www`.

PIP

::

    $ curl http://python-distribute.org/distribute_setup.py | python
    $ curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python

virtualenv

This is optional.  It will keep your python packages in a isolated dir and it helps to keep things organized if the server will be doing other things with python.  If you don't care, feel free to skip this and move on to :ref:`Install Packages`_.

::

    $ pip install virtualenv
    $ virtualenv dev
    $ cd dev
    $ source bin/activate

Now we need to install our python packages.  Installing Frog will add what it needs.

::

    $ pip install django-frog
    $ pip install pillow

Make a folder for static files

::

    $ mkdir /var/www/static
    $ ln -s /usr/local/lib/python27/site-packages/frog/static /var/www/static/frog
    $ mkdir /var/www/dev/migrations
    $ touch /var/www/dev/migrations/__init__.py


Install MySQL
-------------

Ubuntu comes with MySQL 5, so no need to install anything further. We just need the python bindings:

::

    $ apt-get install python-mysqldb

Next we just need to create a database and add a user. For this tutorial, I'll use 'frog' as the database and 'django' as the user:

::

    > mysql -u root -p
    mysql> create database frog;
    mysql> create user 'django'@'localhost' identified by 'django';
    mysql> grant all on frog.* to 'django'@'localhost' identified by 'django';


Install Nginx
-------------

The idea here is that nginx will sit in front of everything. Nginx is a lightweight and fast webserver, though for this tutorial, we'll just be using it to serve static files. So Nginx will redirect traffic to gunicorn when it's a django request and just server the static files when not. Gunicorn will listen on port :8000 and Nginx on port :80.

::

    $ sudo apt-get install nginx

Edit `/etc/nginx/nginx.conf`. You'll only need to edit the server section of the default conf:

::

    ...
    http {
      ...
      log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';
      ...
      server {
          listen       80;
          server_name  dev;
          access_log   logs/www/dev.log  main;

          client_max_body_size 512M;

          # serve django admin files
          # This location may differ based on your setup
          location /media  {
            alias /usr/lib/python2.7/site-packages/django/contrib/admin;
            expires 30d;
          }

          # serve static files
          location /static  {
            alias /var/www/static;
            expires 30d;
          }

          # pass requests for dynamic content
          location / {
            proxy_pass_header Server;
            proxy_set_header Host $http_host;
            proxy_redirect off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Scheme $scheme;
            proxy_connect_timeout 10;
            proxy_read_timeout 10;
            proxy_pass http://127.0.0.1:8000/;
          }
      }
      ...
    }
    ...


Install Gunicorn
----------------

Gunicorn will run all of the django/python stuff behind nginx. We'll need to install it and then write a service script so we can start/stop/restart it quickly.  Install gunicorn:

::

    $ pip install gunicorn

Edit `/var/www/dev/gunicorn.sh`

::

    #!/bin/bash
    set -e
    LOGFILE=/var/log/gunicorn/frog.log
    LOGDIR=$(dirname $LOGFILE)
    NUM_WORKERS=3
    # user/group to run as
    USER=your_unix_user
    GROUP=your_unix_group
    cd /var/www/dev
    test -d $LOGDIR || mkdir -p $LOGDIR
    exec gunicorn dev.wsgi:application \
    --user=$USER --group=$GROUP --log-level=debug \
    --log-file=$LOGFILE 2>>$LOGFILE

Make it executable

::

    chmod ug+x /var/www/dev/gunicorn.sh

Next create an Upstart service, /etc/init/gunicorn.conf

::

    description "Frog Django instance"
    start on runlevel [2345]
    stop on runlevel [06]
    respawn
    respawn limit 10 5
    exec /var/www/dev/gunicorn.sh

Make a symlink to init.d

::

    sudo ln -s /lib/init/upstart-job /etc/init.d/gunicorn


Setup Django
------------

Now we need to configure Django to include Frog and handle our requests.  Edit `/var/www/dev/dev/settings.py` and make the following changes:

::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'frog',
            'USER': 'django',
            'PASSWORD': 'django',
            'HOST': '',
            'PORT': '',
        }
    }
    MEDIA_ROOT = '/var/www/static/'
    MEDIA_URL = 'http://127.0.0.1/static/'
    TEMPLATE_CONTEXT_PROCESSORS = (
     "django.contrib.auth.context_processors.auth",
     "django.core.context_processors.debug",
     "django.core.context_processors.i18n",
     "django.core.context_processors.media",
     "django.core.context_processors.static",
     "django.core.context_processors.tz",
     "django.contrib.messages.context_processors.messages",
     "frog.context_processors.media",
    )
    # Needed for redirect
    LOGIN_URL = '/frog'

    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.comments',
        'haystack',
        'django.contrib.admin',
        'frog',
        'south',
    )
    SOUTH_MIGRATION_MODULES = {
        'frog': 'migrations',
    }

    AUTHENTICATION_BACKENDS = ('frog.auth.SimpleAuthBackend',)
    SESSION_COOKIE_AGE = 31556926 # 1 year

Now add the Frog URLs to `/var/www/dev/dev/urls.py`

::

    ...
    url(r'^frog/', include('frog.urls')),
    ...


Start It
--------

With everything in place, we just need to start it up and cross our fingers

::

    service gunicorn start
    service nginx start

Go to http://server and see if there's a happy Django page