.. _existing:

Existing Django Project
=======================

If you already have a working Django project and you'd like to add Frog to it, please follow these steps


Migrations
----------

Frog uses south to handle its model migrations.  This probably wont come up often, if ever, but should you need to adjust the models, South will be invaluable.  Under your project root:

::

    $ mkdir migrations
    $ touch migrations/__init__.py

Now all Frog's model migrations will be stored here instead of in the site-packages folder.


Install Frog
------------

First use pip to install Frog, it will depend on Django 1.5+ so it may upgrade your installation.  Make sure you are prepared for that!  Also, the paths below are for example only, please make any changes to fit your system.

::

    $ pip install django-frog
    $ ln -s /usr/local/lib/python27/site-packages/frog/static /var/www/static/frog


Settings
--------

Edit your project setting.py file

::

    INSTALLED_APPS = (
        ...
        'haystack', ## -- Haystack must come before admin
        'django.contrib.admin',
        'frog',
        ...
        'south',
    )
    SITE_URL = 'http://servername'
    ## -- Used for creating new users
    DOMAIN = 'yourdomain.com'
    ## -- Path to ffmpeg for processing video
    FFMPEG = 'path/to/ffmpeg'

    SOUTH_MIGRATION_MODULES = {
        'frog': 'migrations',
    }
    
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

Note that the following middlewares need to be enabled:

- django.contrib.sessions.middleware.SessionMiddleware
- django.middleware.csrf.CsrfViewMiddleware
- django.contrib.auth.middleware.AuthenticationMiddleware
- django.contrib.messages.middleware.MessageMiddleware

Also add the Frog URLs to your projects urls.py

::

    ...
    url(r'^frog/', include('frog.urls')),
    ...


Database
--------

Do an initial migration and create the tables to the Frog models

::

    $ python manage.py schemamigration frog --initial
    $ python manage.py migrate frog

That's it, you should be able to go to http://server/frog