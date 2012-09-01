import json
import Queue
import subprocess
import re

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from settings import MEDIA_ROOT, FFMPEG, IMAGE_SIZE_CAP, IMAGE_SMALL_SIZE, THUMB_SIZE

from videoThread import VideoThread, JsonQueue

from path import path as Path
from PIL import Image as pilImage

gMaxSize = IMAGE_SIZE_CAP
gSmallSize = IMAGE_SMALL_SIZE
gThumbSize = THUMB_SIZE

gQueue = Queue.Queue()
gVideoThread = VideoThread(gQueue)
gVideoThread.start()
gJsonQueue = JsonQueue()

DefaultPrefs = {
    'backgroundColor': '000000',
    'tileCount': 6,
    'batchSize': 300,
    'includeImage': True,
    'includeVideo': True,
}


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
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
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

    @staticmethod
    def getUniqueID(path, user):
        path = Path(path)
        username = 'Anonymous' if user.is_anonymous() else user.username
        return '%s_%s' % (username, path.name)

    def getGuid(self):
        return Guid(self.id, self.AssetType)

    def export(self):
        pass

    def getPath(self):
        guid = self.getGuid()
        
        return Path(MEDIA_ROOT) / guid.guid[-2:] / guid.guid

    def getFiles(self):
        path = self.getPath()
        allfiles = path.files()

        thumb = Path(self.thumbnail.name).name.replace(self.hash, self.title)
        source = Path(self.source.name).name.replace(self.hash, self.title)
        files = {}
        files[thumb] = MEDIA_ROOT + '/' + self.thumbnail.name
        files[source] = MEDIA_ROOT + '/' + self.source.name
        
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
            'thumbnail': self.thumbnail.url,
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
        
        self.source = hashPath.replace('\\', '/').replace(MEDIA_ROOT, '')
        galleries = galleries or []
        tags = tags or []
        
        workImage = pilImage.open(MEDIA_ROOT + self.source.name)
        formats = [
            ('image', gMaxSize),
            ('small', gSmallSize),
            ('thumbnail', gThumbSize),
        ]
        for i,n in enumerate(formats):
            if workImage.size[0] > n[1] or workImage.size[1] > n[1]:
                workImage.thumbnail((n[1], n[1]), pilImage.ANTIALIAS)
                dest = self.source.name.replace(hashVal, '_' * i + hashVal)
                setattr(self, n[0], self.source.name.replace(hashVal, '_' * i + hashVal))
                workImage.save(MEDIA_ROOT + getattr(self, n[0]).name)
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

        self.source = hashPath.replace('\\', '/').replace(MEDIA_ROOT, '')
        galleries = galleries or []
        tags = tags or []

        ## -- Get info
        cmd = '%s -i "%s"' % (FFMPEG, hashPath.replace('/', '\\'))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        infoString = proc.stdout.readlines()
        width = 100
        height = 100
        for n in infoString:
            n = n.strip()
            if n.startswith('Stream'):
                dim = n.split(',')[2].strip()
                width, height = dim.split('x')
                width = width.split(' ')[0]
                height = height.split(' ')[0]
                break
        self.width = width
        self.height = height

        ## -- Save thumbnail and put into queue
        thumbnail = Path(hashPath.parent.replace('/', '\\')) / "_%s.jpg" % hashVal
        cmd = '%s -i "%s" -ss 1 -vframes 1 "%s"' % (FFMPEG, hashPath.replace('/', '\\'), thumbnail)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        proc.communicate()

        self.thumbnail = thumbnail.replace('\\', '/').replace(MEDIA_ROOT, '')

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

        self.save()

        gJsonQueue.append(self.json())
        gQueue.put(self)

    def json(self):
        obj = super(Video, self).json()
        obj['source'] = self.source.url if self.source else ''
        obj['video'] = self.video.url if self.video else ''
        obj['video_thumbnail'] = self.video_thumbnail.url if self.video_thumbnail else ''

        return obj


class Gallery(models.Model):
    title = models.CharField(max_length=128)
    images = models.ManyToManyField(Image, blank=True, null=True)
    videos = models.ManyToManyField(Video, blank=True, null=True)
    private = models.BooleanField(default=False)
    owner = models.ForeignKey(User, default=1)
    description = models.TextField(default="")

    class Meta:
        verbose_name_plural = "Galleries"

    def __unicode__(self):
        return self.title

    def json(self):
        obj = {
            'id': self.id,
            'title': self.title,
            'private': self.private,
            'image_count': self.images.count(),
            'video_count': self.videos.count(),
            'owner': {'id': self.owner.id, 'name': self.owner.get_full_name()},
            'description': self.description
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
        1: 1152921504606846976L,
        2: 2305843009213693952L,
    }
    def __init__(self, obj_id, type_id=1):
        if isinstance(obj_id, str):
            self.int = int(obj_id, 16)
            self.guid = obj_id[2:] if obj_id[1] == 'x' else obj_id
        elif isinstance(obj_id, long) or isinstance(obj_id, int):
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


## -- Queue any remaining videos that did not finish prior to restart
for guid in [o['id'] for o in gJsonQueue.data['queued']]:
    gQueue.put(Video.objects.get(pk=guid))