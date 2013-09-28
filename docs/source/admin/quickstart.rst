.. _quickstart:

Quickstart
==========

.. module:: frog.models

This guide is written for windows to get up and running within a few minutes, but is not at all ready for a production server.  If you're on linux, you should be able to follow the instructions below with minimal changes to get up and running.

Requirements
------------

* `Install Python 2.6 or later <http://python.org/download/>`_
* `Install Pillow <https://pypi.python.org/pypi/Pillow/2.1.0#downloads>`_
* :ref:`Install Frog <install>`


Start a project
---------------

First lets open a command line and:

::

    > cd c:\\users\\brett
    > python c:\\python27\\Scripts\\django-admin.py startproject dev
    > cd dev
    > mkdir static
    > mkdir static\\frog
    > copy C:\\python27\\lib\\site-packages\\frog\\static\\* static\\frog


Settings
--------

Now we need to modify the default settings to include Frog and add some other stuff.  The easiest thing to do is just copy and paste the settings file below and make the path changes to fit your machine.  Edit the `c:\\Users\\brett\\dev\\dev\\settings.py` file:

::

    # Django settings for dev project.
    import os
    APPROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    DEBUG = True
    TEMPLATE_DEBUG = DEBUG

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(APPROOT, 'frog.sqlite'),
        }
    }

    SITE_ID = 1

    MEDIA_URL = 'http://127.0.0.1:8000/static/'
    MEDIA_ROOT = os.path.join(APPROOT, 'static') + '\\'

    ADMIN_MEDIA_PREFIX = '/static/admin/'
    SECRET_KEY = 'secret'

    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )

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

    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    )

    ROOT_URLCONF = 'dev.urls'

    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.admin',
        'django.contrib.comments',
        'frog',
    )

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console':{
                'level':'DEBUG',
                'class':'logging.StreamHandler',
            }
        },
        'loggers': {
            'django.request': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': True,
            },
        }
    }

    AUTHENTICATION_BACKENDS = (
        'frog.auth.SimpleAuthBackend',
    )

URLs
----

Next we have to add the Frog URLs so edit the `c:\\Users\\brett\\dev\\dev\\urls.py` file:

::

    from django.conf.urls import patterns, include, url
    from django.conf import settings

    from django.contrib import admin
    admin.autodiscover()

    urlpatterns = patterns(
        '',
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            'show_indexes': True
            }),
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            'show_indexes': True
            }),
        url(r'^frog/', include('frog.urls')),

        url(r'^admin/', include(admin.site.urls)),
    )

Start the Server
----------------

At the command line type in

::

    > python manage.py syncdb
    > python manage.py runserver

Now go to http://127.0.0.1:8000/frog
