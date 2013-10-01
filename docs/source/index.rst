.. frog documentation master file, created by
   sphinx-quickstart on Tue Sep 24 22:33:21 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to frog's documentation!
================================

.. raw:: html

    <div style='width: 100%;text-align: center;'><iframe width="560" height="315" src="http://www.youtube.com/embed/Brfzw7CyuGo" frameborder="0" allowfullscreen></iframe></div>


User Guide
==========

The user guide is for those actually using an instllation of Frog.  It goes over the UI and how to interact and add content.

.. toctree::
   :maxdepth: 1
   
   user/navigation
   user/search_filter
   user/tags

Adding Content
--------------

Adding content to Frog is as simple as dragging stuff from your desktop onto the site.  It will upload and do any conversions neccessary and add them to the current Gallery.  You can also click the Upload button on the toolbar at the top to bring up a familiar file selection dialog.


Developer Guide
===============

.. toctree::
   :maxdepth: 2

   dev/introduction
   dev/views

Admin Guide
===========

.. toctree::
   :maxdepth: 1

   admin/install
   admin/quickstart
   admin/server
   admin/existing
   admin/troubleshooting

Frog Settings
-------------

.. data:: FROG_IMAGE_SIZE_CAP

    The maximum image size to allow for uploads.  Anything larger will be scaled proportionally to fit into a square of this value.

    Default is 5120

.. data:: FROG_IMAGE_SMALL_SIZE

    This value determines what is considered a "small" version of the image

    Default is 600

.. data:: FROG_THUMB_SIZE

    The value to scale thumbnails down to

    Default is 256

.. data:: FROG_UNIQUE_ID

    A string to a module function that will be called to determine a unique value for the image.  This will be used to find and overwrite existing images.  The function should take two arguments, a path and user.  The `path` arg will have as much of the filename as possible and the `user` arg will be a standard Django User instance.  The default is

    ::

        def uniqueid(path, user)
            username = 'Anonymous' if user.is_anonymous() else user.username
            return '%s_%s' % (username, os.path.split(path)[1])

.. data:: FROG_PATH

    A path relative to our MEDIA_ROOT setting where Frog will store it's image and video files

    Default is ''


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

