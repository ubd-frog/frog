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
from optparse import make_option

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from frog.models import Gallery, FROG_SITE_URL

FROG_UPDATE_GROUP_EMAIL = getattr(settings, 'FROG_UPDATE_GROUP_EMAIL', None)
FROG_UPDATE_DAILY_GROUP_EMAIL = getattr(settings, 'FROG_UPDATE_DAILY_GROUP_EMAIL', FROG_UPDATE_GROUP_EMAIL)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--type', '-t',
            dest='intervalType',
            default='weekly',
            help='Frequency type'
        )
        parser.add_argument(
            '--gallery', '-g',
            default=1,
            help='Gallery to send emails about'
        )

    def handle(self, *args, **kwargs):
        if FROG_UPDATE_GROUP_EMAIL is None:
            raise ImproperlyConfigured('FROG_UPDATE_GROUP_EMAIL is required for email updates')

        today = timezone.now()
        interval = kwargs.get('intervalType', 'weekly')
        if interval == 'daily':
            delta = 1
            from_email, to = FROG_UPDATE_DAILY_GROUP_EMAIL, FROG_UPDATE_DAILY_GROUP_EMAIL
        else:
            delta = 7
            from_email, to = FROG_UPDATE_GROUP_EMAIL, FROG_UPDATE_GROUP_EMAIL
        previous = today - datetime.timedelta(delta)

        gallery = Gallery.objects.get(pk=kwargs['gallery'])

        images = gallery.images.filter(created__range=(previous, today))
        videos = gallery.videos.filter(created__range=(previous, today))

        if not images and not videos:
            return

        html = render_to_string(
            'frog/cron_email.html',
            {'images': images, 'videos': videos, 'SITE_URL': FROG_SITE_URL, 'gallery': gallery}
        )
        subject = '{name} ({interval}) for {date}'.format(
            interval=interval.capitalize(),
            name=gallery.title,
            date=today.strftime('%m/%d/%Y'),
        )
        
        text_content = 'Only html supported'
        send_mail(subject, text_content, from_email, [to], html_message=html)
        self.stdout.write('Found {} images and {} videos'.format(len(images), len(videos)))
