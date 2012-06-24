from django.conf.urls import patterns, include, url

from views import gallery, tag, image, video, comment, downloadView, index, pref, frogLogin, frogLogout, switchArtist, isUnique, helpMe, artistLookup
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

    url(r'^$', index),
)
