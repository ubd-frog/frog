##################################################################################################
# Copyright (c) 2012 Brett Dixon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
# Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##################################################################################################

from django.conf.urls import url

# import views
from frog import views

urlpatterns = [
    # -- SSO
    url(r'^auth$', views.auth),
    # -- Gallery
    url(r'^gallery$', views.gallery.index),
    url(r'^gallery/(?P<obj_id>\d+)$', views.gallery.index),
    url(r'^gallery/(?P<obj_id>\d+)/filter$', views.gallery.filterObjects),
    url(r'^gallery/(?P<obj_id>\d+)/subscribe$', views.gallery.subscribe),
    # -- Piece
    url(r'^like/(?P<guid>\w+)$', views.piece.like),
    url(r'^piece/(?P<guid>\w+)/$', views.piece.data),
    url(r'^p$', views.piece.getGuids),
    # -- Tag
    url(r'^tag/$', views.tag.index),
    url(r'^tag/(?P<obj_id>\d+)/$', views.tag.index),
    url(r'^tag/resolve/(?P<name>[\w\s\.\-\`\']+)$', views.tag.resolve),
    url(r'^tag/search$', views.tag.search),
    url(r'^tag/manage$', views.tag.manage),
    url(r'^tag/merge/(?P<obj_id>\d+)/$', views.tag.merge),
    # -- User prefs
    url(r'^pref/$', views.userpref.index),
    # -- Comments
    url(r'^comment/$', views.comment.commentList),
    url(r'^comment/(?P<obj_id>\d+)/$', views.comment.index),
    # -- Misc functions
    url(r'^download$', views.download),
    url(r'^switchartist$', views.switchArtist),
    url(r'^artistlookup$', views.artistLookup),
    url(r'^isunique/$', views.isUnique),
    url(r'^getuser$', views.getUser),
    url(r'^userlist', views.userList),
    url(r'^csrf$', views.csrf),
    url(r'siteconfig', views.siteConfig),
    url(r'clienterror/$', views.clientError),
    url(r'releasenotes$', views.releaseNotes),
    # -- Authentication
    url(r'^login$', views.login_),
    url(r'^logout$', views.logout_),
    url(r'^access_denied', views.accessDenied),

    url(r'^$', views.index),
]
