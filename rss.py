""" RSS """

import json

from django.contrib.syndication.views import Feed
from django.template.loader import render_to_string

from frog.models import Gallery, RSSStorage, Image, Video

from settings import SITE_URL


class Daily(Feed):

    def get_object(self, request, obj_id):
        return Gallery.objects.get(pk=obj_id)

    def title(self, obj):
        return "Frog Gallery :: %s (Daily)" % obj.title

    def link(self, obj):
        return '%s/needLink' % SITE_URL

    def items(self, obj):
        return RSSStorage.objects.filter(gallery=obj, interval='daily')

    def item_title(self, item):
        return item.date.strftime('%A, %b %d')

    def item_description(self, obj):
        data = json.loads(obj.data)

        i = list(Image.objects.filter(id__in=data['image']))
        v = list(Video.objects.filter(id__in=data['video']))

        return render_to_string('frog/rss.html', {'images': i, 'videos': v})

    def item_link(self, item):
        return '%s/item/%i' % (SITE_URL, item.id)


class Weekly(Daily):

    def title(self, obj):
        return "Frog Gallery :: %s (Weekly)" % obj.title

    def items(self, obj):
        return RSSStorage.objects.filter(gallery=obj, interval='weekly')