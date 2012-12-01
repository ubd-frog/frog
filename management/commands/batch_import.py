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
from django.conf import settings

from frog.models import Gallery, RSSStorage, Image, Video, Piece, Tag
from frog.uploader import EXT, User
from frog.path import path as Path
from frog.common import getRoot


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dirnames', '-d',
            action='store_true',
            dest='dirnames',
            default=False,
            help='Use folder names as tags'
        ),
        make_option('--topdir', '-t',
            dest='topdir',
            default='.',
            help='Folder name to stop gathering tags from'
        ),
    )

    def handle(self, *args, **options):
        if options['topdir'] == '.':
            options['topdir'] = args[0]

        FILES = Path(args[0]).walk()
        ALL_EXT = EXT['image'] + EXT['video']
        USER = User.objects.get_or_create(
            username='noauthor',
            defaults={'first_name': 'No', 'last_name': 'Author', 'email': 'none@gmail.com'}
        )[0]
        GALLERY = Gallery.objects.get(pk=1)

        for file_ in FILES:
            if file_.ext.lower() in ALL_EXT:
                uniqueName = Piece.getUniqueID(file_, USER)
                if file_.ext.lower() in EXT['image']:
                    model = Image
                else:
                    model = Video

                obj = model.objects.get_or_create(unique_id=uniqueName, defaults={'author': USER})[0]
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
                obj.gallery_set.add(GALLERY)

                tags = []
                if options['dirnames']:
                    tags = file_.parent.replace(options['topdir'], '').replace('\\', '/').split('/')
                    tags = filter(None, tags)
                
                obj.export(hashVal, hashPath, tags=tags)

                self.stdout.write('Added %s\n' % file_)

