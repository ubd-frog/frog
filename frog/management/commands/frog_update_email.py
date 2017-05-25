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

import datetime
from urlparse import urlparse

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

from frog.models import GallerySubscription, FROG_SITE_URL
from frog.common import getSiteConfig


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--type', '-t',
            dest='intervalType',
            default='weekly',
            help='Frequency type'
        )

    def handle(self, *args, **kwargs):
        siteconfig = getSiteConfig()
        today = timezone.now()
        interval = kwargs.get('intervalType', 'weekly')
        sender = 'notifications@{}'.format(urlparse(settings.FROG_SITE_URL).netloc)
        if interval == 'daily':
            delta = 1
            subs = GallerySubscription.objects.filter(frequency=GallerySubscription.DAILY)
        else:
            delta = 7
            subs = GallerySubscription.objects.filter(frequency=GallerySubscription.WEEKLY)

        for sub in subs:
            html = renderEmail(sub.gallery, delta)
            if html is None:
                continue

            subject = '{site}:{name} ({interval}) for {date}'.format(
                interval=interval.capitalize(),
                name=sub.gallery.title,
                date=today.strftime('%m/%d/%Y'),
                site=siteconfig['name'],
            )

            text_content = ''
            send_mail(subject, text_content, sender, [sub.user.email], html_message=html)


def renderEmail(gallery, delta):
    today = timezone.now()
    previous = today - datetime.timedelta(delta)

    images = gallery.images.filter(created__range=(previous, today))
    videos = gallery.videos.filter(created__range=(previous, today))

    if not images and not videos:
        return

    html = render_to_string(
        'frog/cron_email.html',
        {'images': images, 'videos': videos, 'SITE_URL': FROG_SITE_URL, 'gallery': gallery}
    )

    return html
