import datetime
import json
import shutil

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

import path

from frog import models
from frog import auth_ldap
from frog.common import getHashForFile
from frog.uploader import EXT

MOD_FILE = path.path('/home/brett/Envs/dev/modified.json')


class Command(BaseCommand):
    help = 'Scrapes a dir for new images'

    def add_arguments(self, parser):
        parser.add_argument('dirname', help='Directory to scrape')

    def handle(self, *args, **options):
        users = {}
        p = path.path(options['dirname'])

        if not MOD_FILE.exists():
            MOD_FILE.write_text('{}')

        data = json.loads(MOD_FILE.text())
        auth = auth_ldap.LDAPAuthBackend()

        for username in p.dirs():
            username = username.namebase.lower()
            user = auth.get_or_create(username)
            users[username] = user

        for f in p.walkfiles():
            username = f.relpath(p).split('/')[0].lower()
            user = users[username]
            uniqueid = models.Image.getUniqueID(f, user)
            created = False
            tags = []
            galleries = [1]

            if f.ext.lower() in EXT['image']:
                model = models.Image
            elif f.ext.lower() in EXT['video']:
                model = models.Video
            else:
                #self.stderr.write('Filetype "{}" not supported'.format(f.ext))
                continue
            
            obj, created = model.objects.get_or_create(unique_id=uniqueid, defaults={'author': user})
            
            guid = obj.getGuid()
            with f.open('rb') as fh:
                hashVal = getHashForFile(fh)

            if hashVal == obj.hash:
                continue

            objPath = models.ROOT
            if models.FROG_PATH:
                objPath = objPath / models.FROG_PATH
            objPath = objPath / guid.guid[-2:] / guid.guid / f.name
            hashPath = objPath.parent / hashVal + objPath.ext

            if not objPath.parent.exists():
                objPath.parent.makedirs()

            try:
                f.copy(hashPath)
            except:
                pass
            
            obj.hash = hashVal
            obj.foreign_path = f
            obj.title = objPath.namebase
            self.stdout.write('Exporting {}'.format(f))
            obj.export(hashVal, hashPath, tags=tags, galleries=galleries)

            
            if created:
                self.stdout.write('Added {}'.format(f))
            else:
                self.stdout.write('Updated {}'.format(f))

            
            
            

