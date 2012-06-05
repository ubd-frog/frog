""" batch """

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