.. _quickstart:

Quickstart
==========

.. module:: frog.models

This guide is written for windows to get up and running within a few minutes, but is not at all ready for a production server.  If you're on linux, you should be able to follow the instructions below with minimal changes to get up and running.

The main point of this is to get a quick demo site up and running with minimal input.  Once this quickstart is finished there are a few more steps you may wish to take in order to get a fully functional application running.

Requirements
------------

* `Install Python 2.7 or later <http://python.org/download/>`_
* `Install pip <https://pip.pypa.io/en/stable/installing/>`_
* `Install nginx <https://nginx.org/download/nginx-1.12.2.zip>`_


Setup an Environment
--------------------

It is best practice to use a virtual environment and this quickstart requires that you do.  This is a very simple step and you'll be glad you did it.  First open a cmd prompt where you want to store all of this.  I'll use c:\envs for this example, but feel free to put it wherever you'd like.

Open a cmd prompt at c:\envs and run the following

::

    > pip install virtualenv
    > virtualenv test

This will make a new virtual environment called test at c:\envs\test

::

    > cd test
    > scripts\activate

We can now do whatever we want to this python installation without messing with the system one.

::

    > pip install django-frog

This will go through an install a bunch of things we need.  Once its done, you can finally run

::

    > frog_init

What this does:

* Sets up a basic project with frog ready to go
* Creates a sqlite database with preloaded default data
* Creates an "admin" user
* Creates an nginx configuration file to use

Start the Server
----------------

For frog, we need to services running: one for serving the site and one for converting video files

Web Server

::

    > cd dev
    > python manage.py runserver

Video worker
We'll need a second cmd prompt for this and activate the virtualenv as before

::

    > cd c:\envs\test\dev
    > ..\scripts\activate
    > python manage.py video_worker

Next we just need to run nginx with our conf file to tie it all together.  Open a new cmd prompt to wherever you extracted nginx to.  In this example, I'm using c:\bin\nginx

::

    > cd c:\bin\nginx
    > nginx -c c:\envs\test\dev\frog.conf


Now go to http://127.0.0.1 and you should have a completely operational instance.  Login with "admin" and no password.

Next Steps
----------

As mentioned above, to get this in a more production ready state, you'll probably want to use a production database such as MySQL or Postgres.  You'll also want to use a wsgi server to serve the application.

* gunicorn (linux)
* uwsgi (linux)
* waitress

You can use the dev project generated as a good starting point as it has everything needed to make frog go.  Feel free to teak settings in the `frog_settings.py` file.
