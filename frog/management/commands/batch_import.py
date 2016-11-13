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
from django.contrib.auth import get_user

import path

from frog.models import Gallery, Image, Video, Piece
from frog.uploader import EXT, User
from frog.common import getRoot


CACHE = {}

def getAuthor(username):
    username = username.lower()
    if username not in CACHE:
        CACHE[username] = get_user(username)
    
    return CACHE[username]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path')
        parser.add_argument(
            '--dirnames', '-d',
            action='store_true',
            dest='dirnames',
            default=False,
            help='Use folder names as tags'
        )
        parser.add_argument(
            '--topdir', '-t',
            dest='topdir',
            default='.',
            help='Folder name to stop gathering tags from'
        )
        parser.add_argument(
            '--user', '-u',
            dest='user',
            default='noauthor',
            help='Username to use for images'
        )
        parser.add_argument(
            '--date',
            type=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'),
            help='Items older than this date will not be imported.  Format: YYYY-MM-DD'
        )

    def handle(self, *args, **options):
        if options['topdir'] == '.':
            options['topdir'] = options['path']

        files = path.Path(options['path']).walk()
        extensions = EXT['image'] + EXT['video']
        baseuser = User.objects.get_or_create(
            username=options['user'],
            defaults={'first_name': 'No', 'last_name': 'Author', 'email': 'none@gmail.com'}
        )[0]
        gallery = Gallery.objects.get(pk=1)

        for file_ in files:
            if options['date']:
                d = datetime.datetime.fromtimestamp(file_.mtime)
                if d <= options['date']:
                    self.stdout.write('Skipping {} as it is too old: {}'.format(file_, d))
                    continue

            if file_.ext.lower() in extensions:
                try:
                    user = getAuthor(file_.owner)
                except NotImplementedError:
                    user = baseuser

                uniqueName = Piece.getUniqueID(file_, user)
                if file_.ext.lower() in EXT['image']:
                    model = Image
                else:
                    model = Video

                obj = model.objects.get_or_create(unique_id=uniqueName, defaults={'author': user})[0]
                guid = obj.getGuid()
                hashVal = file_.read_hexhash('sha1')

                objPath = getRoot() / guid.guid[-2:] / guid.guid / file_.name.lower()
                hashPath = objPath.parent / hashVal + objPath.ext
                
                if not objPath.parent.exists():
                    objPath.parent.makedirs()

                file_.copy(hashPath)

                obj.hash = hashVal
                obj.foreign_path = file_
                obj.title = objPath.namebase
                obj.created = datetime.datetime.fromtimestamp(file_.mtime)
                obj.gallery_set.add(gallery)

                tags = []
                if options['dirnames']:
                    tags = file_.parent.replace(options['topdir'], '').replace('\\', '/').split('/')
                    tags = filter(None, tags)
                
                obj.export(hashVal, hashPath, tags=tags)

                self.stdout.write('Added %s\n' % file_)

