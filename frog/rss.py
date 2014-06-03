##################################################################################################
# Copyright (c) 2012 Brett Dixon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
# Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##################################################################################################


import json

from django.contrib.syndication.views import Feed
from django.template.loader import render_to_string

from frog.models import Gallery, RSSStorage, Image, Video, FROG_SITE_URL


class Daily(Feed):

    def get_object(self, request, obj_id):
        return Gallery.objects.get(pk=obj_id)

    def title(self, obj):
        return "Frog Gallery :: %s (Daily)" % obj.title

    def link(self, obj):
        return '%s/needLink' % FROG_SITE_URL

    def items(self, obj):
        return RSSStorage.objects.filter(gallery=obj, interval='daily')

    def item_title(self, item):
        return item.date.strftime('%A, %b %d')

    def item_description(self, obj):
        data = json.loads(obj.data)

        i = list(Image.objects.filter(id__in=data['image']))
        v = list(Video.objects.filter(id__in=data['video']))

        return render_to_string('frog/rss.html', {'images': i, 'videos': v, 'SITE_URL': FROG_SITE_URL})

    def item_link(self, item):
        return '%s/item/%i' % (FROG_SITE_URL, item.id)


class Weekly(Daily):

    def title(self, obj):
        return "Frog Gallery :: %s (Weekly)" % obj.title

    def items(self, obj):
        return RSSStorage.objects.filter(gallery=obj, interval='weekly')