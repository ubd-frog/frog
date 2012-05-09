from django.conf.urls import patterns, include, url

from views import gallery, tag, image, video, downloadView
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

    url(r'^download$', downloadView),

    url(r'^$', uploader.post),
)
