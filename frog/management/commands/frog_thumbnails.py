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

from frog.models import Gallery, Image, Video, Piece
from frog.uploader import User
from frog.common import getRoot


class Command(BaseCommand):
    help = 'Generated thumbnails'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--video',
            action='store_true',
            dest='video',
            default=False,
            help='Generate thumbnails for videos'
        )
        parser.add_argument(
            '--image',
            action='store_true',
            dest='image',
            default=False,
            help='Generate thumbnails for images'
        )

    def handle(self, *args, **options):
        processall = not options.get('image', False) and not options.get('video', False)
        if processall:
            self.stdout.write('Processing all: {}'.format(options))
        
        if options.get('image', False) or processall:
            for image in Image.objects.all():
                self.stdout.write('Generating thumbnail for {}'.format(image))
                try:
                    image.generateThumbnail()
                    image.save()
                except Exception as err:
                    self.stderr.write(str(err))

        if options.get('video', False) or processall:
            for image in Video.objects.all():
                self.stdout.write('Generating thumbnail for {}'.format(image))
                try:
                    image.generateThumbnail()
                    image.save()
                except Exception as err:
                    self.stderr.write(str(err))
