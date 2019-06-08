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
import argparse
import datetime
import json

from optparse import make_option
from django.core.management.base import BaseCommand
from django.utils import timezone

from frog.models import ReleaseNotes


class Command(BaseCommand):
    help = 'Add a new ReleaseNote'

    def add_arguments(self, parser):
        parser.add_argument('content')
        parser.add_argument('-d', '--date', default=None, help='In the format %d/%m/%Y or 31/01/2017 for January 31, 2017')

    def handle(self, *args, **options):
        date = timezone.now()
        datestr = options.get('date')
        if datestr:
            date = datetime.datetime.strptime(datestr, '%d/%m/%Y')

        note = ReleaseNotes(notes=options['content'].replace('\\\\n', '\\').replace('\\n', '\n'))
        note.save()
        note.date = date
        note.save()

        self.stdout.write('Added {}'.format(note))
