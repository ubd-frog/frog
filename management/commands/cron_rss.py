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
        prevDay = thisDay - datetime.timedelta(100)

        galleries = Gallery.objects.all()

        for g in galleries:
            images = g.images.values_list('id', flat=True).filter(created__range=(prevDay, thisDay))
            videos = g.videos.values_list('id', flat=True).filter(created__range=(prevDay, thisDay))

            obj = {
                'image': list(images),
                'video': list(videos),
            }

            rss = RSSStorage()
            rss.date = thisDay
            rss.gallery = g
            rss.type = kwargs['intervalType']
            rss.data = json.dumps(obj)
            rss.save()