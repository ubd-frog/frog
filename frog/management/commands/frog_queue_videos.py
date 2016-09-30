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


from optparse import make_option
from django.core.management.base import BaseCommand

import path

from frog.models import Gallery, Image, Video, Piece, VideoQueue
from frog.uploader import EXT, User
from frog.common import getRoot


class Command(BaseCommand):
    help = 'Generated thumbnails'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'guids',
            nargs='*',
            default=[],
        )

    def handle(self, *args, **options):
        for guid in options['guids']:
            video = Video.objects.get(guid=guid)
            item = VideoQueue.objects.get_or_create(video=video)[0]
            item.video = video
            item.status = VideoQueue.QUEUED
            item.save()
            self.stdout.write('Added: {}'.format(video))
