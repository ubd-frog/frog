.. frog documentation master file, created by
   sphinx-quickstart on Tue Sep 24 22:33:21 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Frog Media Server
=================

Frog Media Server is a server-client solution for sharing and maintaining large collections of images and videos

Accessibility
-------------

.. image:: /_static/acc_info.png
    :align: left
    :height: 300

First and foremost, Frog is easy to use and easy to add media files to. It has a straight forward API so integrating it into any other app or tool is trivial. Users can upload and view media instantly and the entire team benefits. For example, an artist could be working in Photoshop and simply hit a hotkey or panel button that would send a PNG and layered source PSD to Frog. The artist doesn't have to break his workflow just to share images with the rest of the team.

Since Frog is web based, everyone can get to it wherever they are. The viewer is done in HTML5 canvas which makes it even more accessible as no plugins are required.


Visibility
----------

.. image:: /_static/vis_info.png
    :align: left
    :height: 300

One of the biggest problems I see in creative studios is that their media is usually hosted on a network drive somewhere and, if you're lucky, organized in folders. Searching is slow, browsing is near impossible, and sharing is a nightmare. A major benefit with Frog is just having everything visible at one time. Being able to browse all media in one place makes discovery a snap. There is also a sense of progress as users can see a history of the project's art over time.


Discovery
---------

To find images or videos, there is a search bar at the top just as there should be.  You can do full text searches or filter by tags. Adding or removing tags to an image or a group of images is dead simple with a nice drag and drop interface anyone can use. Users can quickly search and filter a set of images, then send that link to others. For example, you could have a set of filters for a certain artist and a specific character. Share that link and you'll always have an up-to-date set of images meeting that criteria.

As mentioned before, when media is stored in a network folder, browsing is cumbersome. If Google has tought us anything, its that search is the only means of finding something when the number of items gets too large. No matter how organized a folder structure may be, search will always be faster and more accessible to users.


User Guide
==========

.. raw:: html

    <div style='width: 100%;text-align: center;'><iframe width="560" height="315" src="http://www.youtube.com/embed/Brfzw7CyuGo" frameborder="0" allowfullscreen></iframe></div>

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

.. note:: If you are installing Frog 1.0 from a previous version, please make sure you change any previous setting to the new ones below.

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

.. data:: FROG_FFMPEG

    Absolute path to ffmpeg

.. data:: FROG_SCRUB_DURATION

    If the video is less than this value, in seconds, then it will be converted so it can be scrubbed frame by frame.  This is slower and takes longer but works well for animations.

    Default is 60

.. data:: FROG_FFMPEG_ARGS

    The argument string sent to ffmpeg to convert a video to a web compatible format.  For advanced use only.

    Default is `-vcodec libx264 -b:v 2500k -acodec libvo_aacenc -b:a 56k -ac 2 -y`

.. data:: FROG_SCRUB_FFMPEG_ARGS

    The argument string sent to ffmpeg to convert a video to a scrubbable, web compatible format.  For advanced use only.

    Default is `-vcodec libx264 -b:v 2500k -x264opts keyint=1:min-keyint=8 -acodec libvo_aacenc -b:a 56k -ac 2 -y`

.. data:: FROG_SITE_URL

    The absolute URL for the host.  This is used in RSS feeds and comments to give absolute URLs to content
