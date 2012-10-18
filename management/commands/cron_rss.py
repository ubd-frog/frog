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


import datetime
import json
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from frog.models import Gallery, RSSStorage


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--type', '-t',
            dest='intervalType',
            default='weekly',
            help='Frequency type'
        ),
    )

    def handle(self, *args, **kwargs):
        thisDay = datetime.date.today()
        if kwargs['intervalType'] == 'daily':
            delta = 1
        else:
            delta = 7
        prevDay = thisDay - datetime.timedelta(delta)

        galleries = Gallery.objects.all()

        for g in galleries:
            images = g.images.values_list('id', flat=True).filter(created__range=(prevDay, thisDay))
            videos = g.videos.values_list('id', flat=True).filter(created__range=(prevDay, thisDay))

            if not images and not videos:
                continue

            obj = {
                'image': list(images),
                'video': list(videos),
            }

            rss = RSSStorage()
            rss.date = thisDay
            rss.gallery = g
            rss.interval = kwargs['intervalType']
            rss.data = json.dumps(obj)
            rss.save()