##################################################################################################
# Copyright (c) 2012 Brett Dixon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
# Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##################################################################################################


import json
import subprocess
import re
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from frog.videoThread import VideoThread, parseInfo, FROG_FFMPEG

from path import path as Path
from PIL import Image as pilImage
import six

from frog import getRoot

FROG_IMAGE_SIZE_CAP = getattr(settings, 'FROG_IMAGE_SIZE_CAP', 5120)
FROG_IMAGE_SMALL_SIZE = getattr(settings, 'FROG_IMAGE_SMALL_SIZE', 600)
FROG_THUMB_SIZE = getattr(settings, 'FROG_THUMB_SIZE', 256)
FROG_UNIQUE_ID = getattr(settings, 'FROG_UNIQUE_ID', None)
FROG_PATH = getattr(settings, 'FROG_PATH', None)
try:
    FROG_SITE_URL = getattr(settings, 'FROG_SITE_URL')
except AttributeError:
    raise ImproperlyConfigured('FROG_SITE_URL is required')

gQueue = Queue()
gVideoThread = VideoThread(gQueue)
gVideoThread.start()

DefaultPrefs = {
    'backgroundColor': '000000',
    'tileCount': 6,
    'batchSize': 300,
    'includeImage': True,
    'includeVideo': True,
}

ROOT = getRoot()

class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey('self', blank=True, null=True)
    artist = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def json(self):
        obj = {
            'id': self.id,
            'name': self.name,
        }

        return obj

    def count(self):
        i = self.image_set.all().count()
        v = self.video_set.all().count()

        return i + v


class Piece(models.Model):
    AssetType = 0
    title = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True, auto_now=True)
    thumbnail = models.ImageField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    foreign_path = models.TextField(blank=True)
    unique_id = models.CharField(max_length=255, blank=True)
    guid = models.CharField(max_length=16, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    deleted = models.BooleanField(default=False)
    hash = models.CharField(max_length=40, blank=True)
    comment_count = models.IntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["-created", "-id"]

    def __unicode__(self):
        return self.title

    def thumbnail_tag(self):
        if self.thumbnail:
            if self.width / self.height > 1:
                return u'<img src="%s" width="256" />' % self.thumbnail.url
            else:
                return u'<img src="%s" height="256" />' % self.thumbnail.url

        return ''
    thumbnail_tag.allow_tags = True
    thumbnail_tag.short_description = 'Image'

    @staticmethod
    def getUniqueID(path, user):
        if FROG_UNIQUE_ID:
            modparts = FROG_UNIQUE_ID.split('.')
            func = modparts.pop()
            mod = '.'.join(modparts)
            imported = __import__(mod, globals(), locals(), [func])
            uid = getattr(imported, func)(path, user)
        else:
            path = Path(path)
            username = 'Anonymous' if user.is_anonymous() else user.username
            uid = '%s_%s' % (username, path.name)

        return uid

    def getGuid(self):
        return Guid(self.id, self.AssetType)

    def export(self):
        pass

    def getPath(self):
        guid = self.getGuid()
        
        return ROOT / guid.guid[-2:] / guid.guid

    def getFiles(self):
        path = self.getPath()
        allfiles = path.files()

        thumb = Path(self.thumbnail.name).name.replace(self.hash, self.title)
        source = Path(self.source.name).name.replace(self.hash, self.title)
        files = {}
        files[thumb] = ROOT + '/' + self.thumbnail.name
        files[source] = ROOT + '/' + self.source.name
        
        for file_ in allfiles:
            if not re.findall('([0-9A-Za-z]{40}\.\w+)', file_):
                files[file_.name] = file_

        return files

    def serialize(self):
        return json.dumps(self.json())

    def tagArtist(self, tag=None):
        ## -- First remove any artist tags
        for n in self.tags.filter(artist=True):
            self.tags.remove(n)
        self.save()
        if tag is None:
            tag = Tag.objects.get_or_create(name=self.author.first_name.lower() + ' ' + self.author.last_name.lower(), defaults={'artist': True})[0]
        
        self.tags.add(tag)
        self.save()

    def json(self):
        obj = {
            'id': self.id,
            'title': self.title,
            'author': {
                'first': self.author.first_name,
                'last': self.author.last_name,
                'username': self.author.username,
                'email': self.author.email,
            },
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
            'width': self.width,
            'height': self.height,
            'guid': self.guid,
            'deleted': self.deleted,
            'hash': self.hash,
            'tags': [tag.json() for tag in self.tags.all()],
            'thumbnail': self.thumbnail.url if self.thumbnail else '',
            'comment_count': self.comment_count,
        }

        return obj


class Image(Piece):
    AssetType = 1
    source = models.ImageField(upload_to='%Y/%m/%d', width_field='width', height_field='height', max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    small = models.ImageField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)

    def export(self, hashVal, hashPath, tags=None, galleries=None):
        '''
        The export function needs to:
        - Move source image to asset folder
        - Rename to guid.ext
        - Save thumbnail, small, and image versions
        '''
        
        self.source = hashPath.replace('\\', '/').replace(ROOT, '')
        galleries = galleries or []
        tags = tags or []

        imagefile = Path(ROOT + self.source.name)
        
        workImage = pilImage.open(imagefile)

        if imagefile.ext in ('.tif', '.tiff'):
            png = imagefile.parent / imagefile.namebase + '.png'
            workImage.save(png)
            workImage = pilImage.open(png)
            imagefile.move(imagefile.replace(self.hash, self.title))
            self.source = png.replace(ROOT, '')

        formats = [
            ('image', FROG_IMAGE_SIZE_CAP),
            ('small', FROG_IMAGE_SMALL_SIZE),
            ('thumbnail', FROG_THUMB_SIZE),
        ]
        for i,n in enumerate(formats):
            if workImage.size[0] > n[1] or workImage.size[1] > n[1]:
                workImage.thumbnail((n[1], n[1]), pilImage.ANTIALIAS)
                setattr(self, n[0], self.source.name.replace(hashVal, '_' * i + hashVal))
                workImage.save(ROOT + getattr(self, n[0]).name)
            else:
                setattr(self, n[0], self.source)

        for gal in galleries:
            g = Gallery.objects.get(pk=int(gal))
            g.images.add(self)

        self.tagArtist()

        for tagName in tags:
            tag = Tag.objects.get_or_create(name=tagName)[0]
            self.tags.add(tag)

        if not self.guid:
            self.guid = self.getGuid().guid
        self.save()

    def json(self):
        obj = super(Image, self).json()
        obj['source'] = self.source.url if self.source else ''
        obj['image'] = self.image.url if self.image else ''
        obj['small'] = self.small.url if self.small else ''

        return obj


class Video(Piece):
    AssetType = 2
    source = models.FileField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    video = models.FileField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    video_thumbnail = models.FileField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)

    def export(self, hashVal, hashPath, tags=None, galleries=None):
        '''
        The export function needs to:
        - Move source image to asset folder
        - Rename to guid.ext
        - Save thumbnail, video_thumbnail, and MP4 versions.  If the source is already h264, then only transcode the thumbnails
        '''

        self.source = hashPath.replace('\\', '/').replace(ROOT, '')
        galleries = galleries or []
        tags = tags or []

        ## -- Get info
        cmd = '%s -i "%s"' % (FROG_FFMPEG, hashPath)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        infoString = proc.stdout.readlines()
        videodata = parseInfo(infoString)
        
        self.width = int(videodata['video'][0]['width'])
        self.height = int(videodata['video'][0]['height'])

        ## -- Save thumbnail and put into queue
        thumbnail = hashPath.parent / ("_%s.jpg" % hashVal)
        cmd = '%s -i "%s" -ss 1 -vframes 1 "%s"' % (
            FROG_FFMPEG,
            hashPath,
            thumbnail
        )
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        proc.communicate()

        self.thumbnail = thumbnail.replace('\\', '/').replace(ROOT, '')

        for gal in galleries:
            g = Gallery.objects.get(pk=int(gal))
            g.videos.add(self)

        artistTag = Tag.objects.get_or_create(name=self.author.first_name + ' ' + self.author.last_name)[0]
        self.tags.add(artistTag)

        for tagName in tags:
            tag = Tag.objects.get_or_create(name=tagName)[0]
            self.tags.add(tag)

        if not self.guid:
            self.guid = self.getGuid().guid

        ## -- Set the temp video while processing
        self.video = 'frog/i/queued.mp4'
        queuedvideo = VideoQueue.objects.get_or_create(video=self)[0]
        queuedvideo.save()

        self.save()

        gQueue.put(self)

    def json(self):
        obj = super(Video, self).json()
        obj['source'] = self.source.url if self.source else ''
        obj['video'] = self.video.url if self.video else ''
        obj['video_thumbnail'] = self.video_thumbnail.url if self.video_thumbnail else ''

        return obj


class VideoQueue(models.Model):
    QUEUED, PROCESSING, COMPLETED, ERROR = (0, 1, 2, 3)
    STATUS = (
        (QUEUED, 'Queued'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (ERROR, 'Error'),
    )

    video = models.OneToOneField(Video, related_name='queue')
    status = models.SmallIntegerField(default=QUEUED, choices=STATUS)
    message = models.TextField(blank=True, null=True)

    def setStatus(self, status):
        self.status = status
        self.save()

    def setMessage(self, message):
        self.message = message
        self.save()


class Gallery(models.Model):
    PUBLIC, PRIVATE, PERSONAL = (0, 1, 2)
    SECURITY_LEVEL = (
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
        (PERSONAL, 'Personal'),
    )
    title = models.CharField(max_length=128)
    images = models.ManyToManyField(Image, blank=True, null=True)
    videos = models.ManyToManyField(Video, blank=True, null=True)
    security = models.SmallIntegerField(default=PUBLIC, choices=SECURITY_LEVEL)
    owner = models.ForeignKey(User, default=1)
    description = models.TextField(default="", blank=True)
    uploads = models.BooleanField(default=True)
    parent = models.ForeignKey('self', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Galleries"

    def __unicode__(self):
        return self.title

    def json(self):
        obj = {
            'id': self.id,
            'title': self.title,
            'security': self.security,
            'image_count': self.images.count(),
            'video_count': self.videos.count(),
            'owner': {'id': self.owner.id, 'name': self.owner.get_full_name()},
            'description': self.description,
            'uploads': self.uploads,
            'iconCls': 'gallery-nav',
            'values': [g.json() for g in self.gallery_set.all()],
            'parent': self.parent.id if self.parent else None,
        }

        return obj


class UserPref(models.Model):
    user = models.ForeignKey(User, related_name='frog_prefs')
    data = models.TextField(default='{}')

    def json(self):
        return json.loads(self.data)

    def setKey(self, key, val):
        data = json.loads(self.data)
        keys = key.split('.')
        keys.reverse()
        name = data
        while keys:
            root = keys.pop()
            name.setdefault(root, {})
            if len(keys) == 0:
                name[root] = val
            else:
                name = name[root]
        self.data = json.dumps(data)
        
        self.save()


class Guid(object):
    AssetTypes = {
        1: 1152921504606846976,
        2: 2305843009213693952,
    }
    def __init__(self, obj_id, type_id=1):
        if isinstance(obj_id, str):
            self.int = int(obj_id, 16)
            self.guid = obj_id[2:] if obj_id[1] == 'x' else obj_id
        elif isinstance(obj_id, six.integer_types):
            self.int = self.AssetTypes[type_id] + obj_id
            self.guid = hex(self.int)[2:-1]
        else:
            self.int = 0
            self.guid = ''


class RSSStorage(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    interval = models.CharField(max_length=6)
    data = models.TextField()
    gallery = models.ForeignKey(Gallery, related_name='rss_storage')
