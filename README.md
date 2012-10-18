Frog
====

Frog is released under the MIT license. It is simple and easy to understand and places almost no restrictions on what you can do with Frog.
[More Information](http://en.wikipedia.org/wiki/MIT_License)

Some portions of Frog utilize GPL or LGPL code or apps:
* Plupload under GPL2
* ExtJS under GPL3
* ffmpeg under LGPL

Frog is a Server and Client solution for hosting and serving media files.  The initial build was intended for creative studios, but could be used for anything, even a home solution.  It was not meant for a front facing tool as the bandwidth costs would be outrageous.

With Frog there are a few key points that make it a perfect solution for your team(s) creative uses.

Accessibility
-------------

First and foremost, Frog is easy to use and easy to add media files to.  It has a straight forward API so integrating it into any other app or tool is trivial.  Users can upload and view media instantly and the entire team benefits.  For example, an artist could be working in Photoshop and simply hit a hotkey or panel button that would send a PNG and layered source PSD to Frog.  The artist doesn't have to break his workflow just to share images with the rest of the team.

Since Frog is web based, everyone can get to it wherever they are.  The viewer is done in HTML5 canvas which makes it een more accissible due to no flash or other plugin requirements.

Visibility
----------

One of the biggest problems I see in creative studios is that their media is usually hosted on a network drive somewhere and, if you're lucky, organized in folders.  Searching is slow, brosing is near impossible, and sharing is a nightmare.  One unseen benefit with Frog is just having everything visible at one time.  Being able to browse all media in one place makes discovery a snap.  There is also a sense of progress and users can see a history of the project's art over time.

Search and Filter
-----------------

The search solution can be configured to use a full featured engine such a Solr or it can use the search capabilities fo the database.  Filtering is done byt he use of Tags.  Tags can be easily added to or removed from a set of images.  Users can quickly search and filter a set of images, then send that link to others.  For example, you could have a set of filters for a certain artist and a specific character.  Share that link and you'll always have an up-to-date set of images meeting that criteria.

As mentioned before, when media is stored in a network folder, browsing is cumbersome.  If Google has tought us anything, its that search is the only means of finding something when the numbers of items gets too large.  So no matter how organized the folder structure is, search will always be faster and more accissible to users.

Open
----

Frog is all open sourced and under the MIT license.  So feel free to modify it to fit your specific needs.  Because it uses Django, it is easy to add features.  The auth system included with Frog is pretty simple.  In fact it's almost 100% honor system due to the site's internal focus.  But adding a more sophisticated authentication system is trivial that to Django.