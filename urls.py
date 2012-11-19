"""
Copyright (c) 2012 Brett Dixon

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
Software, and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


from django.conf.urls import patterns, include, url

from views import gallery, tag, image, video, comment, downloadView, index, pref, frogLogin, frogLogout, switchArtist, isUnique, helpMe, artistLookup, getUser
from rss import Daily, Weekly
from uploader import uploader

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^gallery$', gallery.index),
    url(r'^gallery/(?P<obj_id>\d+)$', gallery.view),
    url(r'^gallery/(?P<obj_id>\d+)/filter$', gallery.filter),

    url(r'^image/(?P<obj_id>\d+)$', image.view),
    url(r'^video/(?P<obj_id>\d+)$', video.view),

    url(r'^tag/$', tag.index),
    url(r'^tag/search$', tag.search),
    url(r'^tag/(?P<obj_id>\d+)$', tag.view),
    url(r'^tag/manage$', tag.manage),

    url(r'^pref/$', pref.index),

    url(r'^comment/$', comment.index),
    url(r'^comment/(?P<obj_id>\d+)$', comment.view),

    url(r'^download$', downloadView),

    url(r'^help/', helpMe),

    url(r'^rss/(?P<obj_id>\d+)/daily$', Daily()),
    url(r'^rss/(?P<obj_id>\d+)/weekly$', Weekly()),

    url(r'^login$', frogLogin),
    url(r'^logout$', frogLogout),

    url(r'^switchartist$', switchArtist),
    url(r'^artistlookup$', artistLookup),
    url(r'^isunique$', isUnique),
    url(r'^getuser$', getUser),

    url(r'^$', index),
)
