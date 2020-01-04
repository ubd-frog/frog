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
import math
import logging

from django.db import models, IntegrityError
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import get_storage_class

from path import Path
from PIL import Image as pilImage
import six
import psd_tools

from frog import getRoot

FROG_IMAGE_SIZE_CAP = getattr(settings, 'FROG_IMAGE_SIZE_CAP', 5120)
FROG_IMAGE_SMALL_SIZE = getattr(settings, 'FROG_IMAGE_SMALL_SIZE', 600)
FROG_THUMB_SIZE = getattr(settings, 'FROG_THUMB_SIZE', 256)
FROG_UNIQUE_ID = getattr(settings, 'FROG_UNIQUE_ID', None)
FROG_PATH = getattr(settings, 'FROG_PATH', None)
FROG_VIDEO_WORK = Path(getattr(settings, 'FROG_VIDEO_WORK', '/tmp/frog_video.json'))
PANORAMIC_MAX = 23000
try:
    FROG_FFMPEG = getattr(settings, 'FROG_FFMPEG')
    FROG_FFPROBE = getattr(settings, 'FROG_FFPROBE')
except AttributeError:
    raise ImproperlyConfigured('FROG_FFMPEG and FROG_FFPROBE are required')
try:
    FROG_SITE_URL = getattr(settings, 'FROG_SITE_URL')
except AttributeError:
    raise ImproperlyConfigured('FROG_SITE_URL is required')

DefaultPrefs = {
    'backgroundColor': '#000000',
    'tileCount': 9,
    'emailComments': True,
    'emailLikes': True,
    'thumbnailPadding': 0,
    'semiTransparent': False,
    'showTags': False,
    'orderby': 'created',
    'largeThumbnails': False,
    'slideshowRandomize': True,
    'slideshowPlayVideo': True,
    'slideshowDuration': 5,
}
FILE_TYPES = {
    'image': ['.jpg', '.png', '.gif', '.tif', '.tiff', '.psd', '.tga'],
    'video': ['.mp4', '.avi', '.wmv', '.mov'],
    'marmoset': ['.mview'],
}
LOGGER = logging.getLogger('frog')


def cropBox(width, height):
    size = FROG_THUMB_SIZE
    if width < size and height < size:
        size = min(width, height)
    ratio = float(width) / float(height)
    if ratio >= 1.0:
        w = size * ratio
        h = size
        box = (
            int(math.floor(width / 2.0 - (size / 2.0))),
            0,
            int(math.floor(width / 2.0 + (size / 2.0))),
            size
        )
    else:
        w = size
        h = size / ratio
        box = (
            0,
            int(math.floor(height / 2.0 - (size / 2.0))),
            size,
            int(math.floor(height / 2.0 + (size / 2.0))),
        )

    return box, w, h


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    artist = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def json(self):
        obj = {
            'id': self.id,
            'name': self.name,
            'artist': self.artist,
            'count': self.count if hasattr(self, 'count') else 0,
        }

        return obj


@python_2_unicode_compatible
class Piece(models.Model):
    AssetType = 0
    title = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    thumbnail = models.ImageField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    custom_thumbnail = models.ImageField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    foreign_path = models.TextField(blank=True)
    unique_id = models.CharField(max_length=255, blank=True)
    guid = models.CharField(max_length=16, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    deleted = models.BooleanField(default=False)
    hash = models.CharField(max_length=40, blank=True)
    comment_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    hidden = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["-created", "-id"]

    def __str__(self):
        return self.title

    def thumbnail_tag(self):
        thumbnail = self.custom_thumbnail or self.thumbnail

        if thumbnail:
            if max(self.width, 1) / max(self.height, 1) > 1:
                return '<img src="%s" style="max-width: 256px;" />' % thumbnail.url
            else:
                return '<img src="%s" style="max-height: 256px;" />' % thumbnail.url

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
            username = 'Anonymous' if user.is_anonymous else user.username
            uid = '%s_%s' % (username, path.name)

        return uid

    @staticmethod
    def fromGuid(guid):
        models = (Image, Video, Group, Marmoset)
        index = int(guid[0])
        for model in models:
            if index == model.AssetType:
                return model.objects.get(guid=guid)

    def getGuid(self):
        return Guid(self.id, self.AssetType)

    def export(self, *args, **kwargs):
        raise NotImplementedError

    def getPath(self, relative=False):
        guid = self.getGuid()

        if relative:
            return Path(guid.guid[-2:]) / guid.guid
        return getRoot() / guid.guid[-2:] / guid.guid

    def getFiles(self):
        path = self.getPath()
        allfiles = path.files()

        thumb = Path(self.thumbnail.name).name.replace(self.hash, self.title).replace('\\', '/')
        source = Path(self.source.name).name.replace(self.hash, self.title).replace('\\', '/')
        files = {}
        files[thumb] = getRoot() + self.thumbnail.name
        files[source] = getRoot() + self.source.name

        if not files[thumb].exists():
            del files[thumb]

        if not files[source].exists():
            del files[source]

        for file_ in allfiles:
            if not re.findall('([0-9A-Za-z]{40}\.\w+)', file_):
                files[file_.name] = file_.replace('\\', '/')

        return files

    def serialize(self):
        return json.dumps(self.json())

    def tagArtist(self, tag=None):
        # -- First remove any artist tags
        for n in self.tags.filter(artist=True):
            self.tags.remove(n)

        if tag is None:
            name = self.author.get_full_name().lower()
            try:
                tag = Tag.objects.get(name__iexact=name, artist=True)
            except ObjectDoesNotExist:
                tag = Tag(name=name, artist=True)
                tag.save()

        self.tags.add(tag)
        self.save()

    def json(self):
        thumbnail = ''
        if self.custom_thumbnail:
            thumbnail = self.custom_thumbnail.url
        elif self.thumbnail:
            thumbnail = self.thumbnail.url

        obj = {
            'id': self.id,
            'title': self.title,
            'author': {
                'id': self.author.id,
                'first': self.author.first_name,
                'last': self.author.last_name,
                'username': self.author.username,
                'name': self.author.get_full_name(),
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
            'thumbnail': thumbnail,
            'custom_thumbnail': bool(self.custom_thumbnail),
            'comment_count': self.comment_count,
            'like_count': self.like_count,
            'description': self.description,
            'hidden': self.hidden,
            'view_count': self.view_count,
        }

        return obj

    def like(self, request):
        try:
            Like.objects.create(user=request.user, content_object=self)
            self.like_count += 1
            self.save()

            return True
        except IntegrityError:
            return False


class Image(Piece):
    AssetType = 1
    source = models.ImageField(upload_to='%Y/%m/%d', width_field='width', height_field='height', max_length=255,
                               blank=True, null=True)
    image = models.ImageField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    group = GenericRelation('GroupChild')
    panoramic = models.BooleanField(default=False)

    def export(self, hashVal=None, hashPath=None, tags=None, galleries=None):
        """
        The export function needs to:
        - Move source image to asset folder
        - Rename to guid.ext
        - Save thumbnail, small, and image versions
        """
        hashVal = hashVal or self.hash
        hashPath = hashPath or self.parent / hashVal + self.ext
        
        source = hashPath.replace('\\', '/').replace(getRoot(), '')
        galleries = galleries or []
        tags = tags or []

        imagefile = getRoot() / source

        if imagefile.ext == '.psd':
            psd = psd_tools.PSDImage.load(imagefile)
            workImage = psd.as_PIL()
        else:
            workImage = pilImage.open(imagefile)
            self.source = source

        if imagefile.ext in ('.tif', '.tiff', '.psd', '.tga'):
            png = imagefile.parent / '{}.png'.format(imagefile.namebase)
            workImage.save(png)
            workImage = pilImage.open(png)
            imagefile.move(imagefile.replace(self.hash, self.title))
            self.source = png.replace(getRoot(), '')

        # -- Panoramic Check
        self.panoramic = 'GPano' in workImage.info.get('XML:com.adobe.xmp', '')
        if not self.panoramic:
            try:
                self.panoramic = any('gpano' in str(_[1]).lower() for _ in workImage.applist)
            except AttributeError:
                pass

        maxsize = PANORAMIC_MAX if self.panoramic else FROG_IMAGE_SIZE_CAP
        if workImage.size[0] > maxsize or workImage.size[1] > maxsize:
            workImage.thumbnail((maxsize, maxsize), pilImage.ANTIALIAS)
            self.image = self.source.name.replace(hashVal, '_{}'.format(hashVal))
            workImage.save(getRoot() + self.image.name)
        else:
            self.image = self.source

        self.generateThumbnail()

        for gal in galleries:
            g = Gallery.objects.get(pk=int(gal))
            g.images.add(self)
            for tag in g.tags.all():
                self.tags.add(tag)

        self.tagArtist()

        for tagName in tags:
            tag = Tag.objects.get_or_create(name=tagName)[0]
            self.tags.add(tag)

        if not self.guid:
            self.guid = self.getGuid().guid

        # -- Posix paths only
        self.source = self.source.name.replace('\\', '/')
        self.image = self.image.name.replace('\\', '/')
        self.thumbnail = self.thumbnail.name.replace('\\', '/')

        self.save()

    def json(self):
        obj = super(Image, self).json()
        obj['source'] = self.source.url if self.source else ''
        obj['image'] = self.image.url if self.image else ''
        obj['panoramic'] = self.panoramic

        return obj

    def generateThumbnail(self):
        """Generates a square thumbnail"""
        image = pilImage.open(getRoot() / self.source.name)
        box, width, height = cropBox(self.width, self.height)

        # Resize
        image.thumbnail((width, height), pilImage.ANTIALIAS)
        # Crop from center
        box = cropBox(*image.size)[0]
        image = image.crop(box)
        # save
        self.thumbnail = self.source.name.replace(self.hash, '{0}{1}'.format('_' * 3, self.hash))
        image.save(getRoot() / self.thumbnail.name)


class Video(Piece):
    AssetType = 2
    source = models.FileField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    video = models.FileField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    video_thumbnail = models.FileField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    poster = models.ImageField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)
    framerate = models.IntegerField(default=24)
    duration = models.FloatField(default=0.0)

    def export(self, hashVal, hashPath, tags=None, galleries=None):
        """
        The export function needs to:
        - Move source image to asset folder
        - Rename to guid.ext
        - Save thumbnail, video_thumbnail, and MP4 versions.  If the source is already h264, then only transcode the thumbnails
        """

        self.source = hashPath.replace('\\', '/').replace(getRoot(), '')
        galleries = galleries or []
        tags = tags or []

        # -- Get info
        videodata = self.info()
        self.width = videodata['width']
        self.height = videodata['height']
        self.framerate = videodata['framerate']
        self.duration = videodata['duration']

        self.generateThumbnail()

        for gal in galleries:
            g = Gallery.objects.get(pk=int(gal))
            g.videos.add(self)
            for tag in g.tags.all():
                self.tags.add(tag)

        self.tagArtist()

        for tagName in tags:
            tag = Tag.objects.get_or_create(name=tagName)[0]
            self.tags.add(tag)

        if not self.guid:
            self.guid = self.getGuid().guid

        # -- Posix paths only
        self.source = self.source.name.replace('\\', '/')
        self.poster = self.poster.name.replace('\\', '/')
        self.thumbnail = self.thumbnail.name.replace('\\', '/')

        self.save()

        # -- Set the temp video while processing
        queuedvideo = VideoQueue.objects.get_or_create(video=self)[0]
        queuedvideo.save()

        try:
            item = VideoQueue()
            item.video = self
            item.save()
        except IntegrityError:
            # -- Already queued
            pass

    def json(self):
        obj = super(Video, self).json()
        obj['source'] = self.source.url if self.source else ''
        obj['video'] = self.video.url if self.video else ''
        obj['video_thumbnail'] = self.video_thumbnail.url if self.video_thumbnail else ''
        obj['poster'] = self.poster.url if self.poster else ''
        obj['framerate'] = self.framerate
        obj['duration'] = self.duration

        return obj

    def generateThumbnail(self):
        """Generates a square thumbnail"""
        source = getRoot() / self.source.name
        thumbnail = source.parent / '_{}.jpg'.format(source.namebase)

        # -- Save thumbnail and put into queue
        poster = source.parent / '__{}.jpg'.format(source.namebase)
        cmd = [FROG_FFMPEG, '-i', str(source), '-vframes', '1', str(thumbnail), '-y']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        proc.communicate()
        image = pilImage.open(thumbnail)
        image.save(poster)
        self.poster = poster.replace(getRoot(), '')

        box, width, height = cropBox(self.width, self.height)

        # Resize
        image.thumbnail((width, height), pilImage.ANTIALIAS)
        # Crop from center
        box = cropBox(*image.size)[0]
        image = image.crop(box)
        # save
        self.thumbnail = thumbnail.replace(getRoot(), '')
        image.save(thumbnail)

    def info(self):
        cmd = [
            FROG_FFPROBE,
            '-select_streams', 'v:0', '-show_entries', 'stream=width,height,codec_name,duration,avg_frame_rate',
            '-of', 'json',
            Path(getRoot()) / self.source.file.name
        ]
        try:
            output = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as err:
            output = ''

        rawdata = json.loads(output)
        framerates = rawdata['streams'][0]['avg_frame_rate'].split('/')
        if len(framerates) == 2:
            framerate = int(framerates[0]) / (int(framerates[1]) or 1)
        else:
            framerate = int(framerates[0])

        data = {
            'width': rawdata['streams'][0]['width'],
            'height': rawdata['streams'][0]['height'],
            'framerate': framerate or 30,
            'codec': rawdata['streams'][0]['codec_name'].lower(),
            'duration': float(rawdata['streams'][0]['duration']),
        }

        return data


class Group(Piece):
    AssetType = 4

    def delete(self, using=None, keep_parents=False):
        for _ in self.children:
            _.hidden = False
            _.save()

        return super(Group, self).delete(using, keep_parents)

    @property
    def children(self):
        return [_.content_object for _ in self.groupchild_set.all()]

    @property
    def source(self):
        return self.children[0].source

    def export(self, hashVal, hashPath, tags=None, galleries=None):
        """"""
        galleries = galleries or []
        tags = tags or []

        for gal in galleries:
            g = Gallery.objects.get(pk=int(gal))
            g.videos.add(self)
            for tag in g.tags.all():
                self.tags.add(tag)

        self.tagArtist()

        for tagName in tags:
            tag = Tag.objects.get_or_create(name=tagName)[0]
            self.tags.add(tag)

        if not self.guid:
            self.guid = self.getGuid().guid

        # -- Posix paths only
        self.save()

    def json(self):
        obj = super(Group, self).json()
        obj['children'] = [_.json() for _ in self.children]

        return obj

    def insertChild(self, index, child):
        children = list(self.groupchild_set.all())
        guids = [_.content_object.guid for _ in children]
        if child.guid in guids:
            childindex = guids.index(child.guid)
            gc = children[childindex]
            children.pop(childindex)
        else:
            gc = GroupChild(group=self, content_object=child)

        children.insert(index, gc)

        tags = []
        for i, _ in enumerate(children):
            tags += _.content_object.tags.all()
            _.index = i
            _.content_object.hidden = True
            _.content_object.save()
            _.save()

        self.width = children[0].content_object.width
        self.height = children[0].content_object.height
        self.save()

        for tag in set(tags):
            self.tags.add(tag)

    def appendChild(self, child):
        self.insertChild(self.groupchild_set.all().count(), child)

    def removeChild(self, child):
        children = list(self.groupchild_set.all())
        guids = [_.content_object.guid for _ in children]
        if child.guid not in guids:
            raise ValueError('Group.removeChild(x): x not in list')

        childindex = guids.index(child.guid)
        gc = children.pop(childindex)
        gc.content_object.hidden = False
        gc.content_object.save()
        gc.delete()

        for i, _ in enumerate(children):
            _.index = i
            _.save()

        if children:
            self.width = children[0].content_object.width
            self.height = children[0].content_object.height
            self.save()


class Marmoset(Piece):
    AssetType = 6
    source = models.FileField(upload_to='%Y/%m/%d', max_length=255, blank=True, null=True)

    def export(self, hashVal, hashPath, tags=None, galleries=None):
        """"""

        self.source = hashPath.replace('\\', '/').replace(getRoot(), '')
        galleries = galleries or []
        tags = tags or []

        self.generateThumbnail()

        for gal in galleries:
            g = Gallery.objects.get(pk=int(gal))
            g.marmosets.add(self)
            for tag in g.tags.all():
                self.tags.add(tag)

        self.tagArtist()

        for tagName in tags:
            tag = Tag.objects.get_or_create(name=tagName)[0]
            self.tags.add(tag)

        if not self.guid:
            self.guid = self.getGuid().guid

        # -- Posix paths only
        self.source = self.source.name.replace('\\', '/')
        self.save()

    def json(self):
        obj = super(Marmoset, self).json()
        obj['source'] = self.source.url if self.source else ''
        if self.custom_thumbnail:
            obj['thumbnail'] = self.custom_thumbnail.url

        return obj

    def generateThumbnail(self, image=None, box=None):
        """Generates a square thumbnail"""


class VideoQueue(models.Model):
    QUEUED, PROCESSING, COMPLETED, ERROR = (0, 1, 2, 3)
    STATUS = (
        (QUEUED, 'Queued'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (ERROR, 'Error'),
    )

    video = models.OneToOneField(Video, related_name='queue', on_delete=models.CASCADE)
    status = models.SmallIntegerField(default=QUEUED, choices=STATUS)
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return '<VideoQueue: {}:{}>'.format(self.video, self.status)


class Gallery(models.Model):
    PUBLIC, PRIVATE, PERSONAL, GUARDED = range(4)
    SECURITY_LEVEL = (
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
        (PERSONAL, 'Personal'),
        (GUARDED, 'Guarded'),
    )
    title = models.CharField(max_length=128)
    images = models.ManyToManyField(Image, blank=True)
    videos = models.ManyToManyField(Video, blank=True)
    groups = models.ManyToManyField(Group, blank=True)
    marmosets = models.ManyToManyField(Marmoset, blank=True)

    security = models.SmallIntegerField(default=PUBLIC, choices=SECURITY_LEVEL)
    owner = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
    description = models.TextField(default="", blank=True)
    uploads = models.BooleanField(default=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        verbose_name_plural = "Galleries"

    def __str__(self):
        return self.title

    def json(self):
        obj = {
            'id': self.id,
            'title': self.title,
            'security': self.security,
            'owner': {'id': self.owner.id, 'name': self.owner.get_full_name()},
            'description': self.description,
            'uploads': self.uploads,
            'iconCls': 'gallery-nav',
            'parent': self.parent.id if self.parent else None,
            'tags': [tag.json() for tag in self.tags.all()],
        }

        return obj

    def addItems(self, items):
        if not items:
            return

        images = [_ for _ in items if isinstance(_, Image)]
        videos = [_ for _ in items if isinstance(_, Video)]
        groups = [_ for _ in items if isinstance(_, Group)]
        marmosets = [_ for _ in items if isinstance(_, Marmoset)]

        self.images.add(*images)
        self.videos.add(*videos)
        self.groups.add(*groups)
        self.marmosets.add(*marmosets)

    def removeItems(self, items):
        if not items:
            return

        images = [_ for _ in items if isinstance(_, Image)]
        videos = [_ for _ in items if isinstance(_, Video)]
        groups = [_ for _ in items if isinstance(_, Group)]
        marmosets = [_ for _ in items if isinstance(_, Marmoset)]

        self.images.remove(*images)
        self.videos.remove(*videos)
        self.groups.remove(*groups)
        self.marmosets.remove(*marmosets)


class UserPref(models.Model):
    user = models.ForeignKey(User, related_name='frog_prefs', on_delete=models.CASCADE)
    data = models.TextField(default=json.dumps(DefaultPrefs))
    clearance = models.SmallIntegerField(default=Gallery.PUBLIC, choices=Gallery.SECURITY_LEVEL)

    def __str__(self):
        return '<UserPref: {}>'.format(self.user.username)

    def json(self):
        temp = DefaultPrefs.copy()
        temp.update(json.loads(self.data))

        return temp

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
    BASE = 1152921504606846976

    def __init__(self, obj_id, type_id=1):
        if isinstance(obj_id, str):
            self.int = int(obj_id, 16)
        elif isinstance(obj_id, six.integer_types):
            self.int = self.BASE * type_id + obj_id
        self.guid = format(self.int, 'x')

    def __str__(self):
        return '<GUID: {}:{}>'.format(self.int, self.guid)


class Like(models.Model):
    user = models.ForeignKey(User, related_name='like_user', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType,
                                     verbose_name='content_type',
                                     related_name='content_type_set_for_%(class)s',
                                     on_delete=models.CASCADE)
    object_pk = models.PositiveIntegerField()
    content_object = GenericForeignKey(ct_field='content_type', fk_field='object_pk')

    class Meta:
        # make sure we can't have a user liking an object more than once
        unique_together = (('user', 'content_type', 'object_pk'),)

    def json(self):
        return {
            'user': self.user.id,
            'date': self.date.isoformat(),
            'object_guid': self.content_object.guid,
        }


class GallerySubscription(models.Model):
    WEEKLY, DAILY = range(2)
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    frequency = models.SmallIntegerField(default=WEEKLY)

    def __str__(self):
        return '<GallerySubscription: {}:{}:{}>'.format(self.user, self.gallery, self.frequency)

    def json(self):
        return {
            'id': self.id,
            'gallery': self.gallery.json(),
            'user': self.user.id,
            'frequency': self.frequency,
        }


class ReleaseNotes(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField()

    def __str__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.id)

    def json(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'notes': self.notes,
        }


class GroupChild(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    index = models.SmallIntegerField(default=0)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    class Meta:
        unique_together = (('group', 'content_type', 'object_id'),)
        ordering = ('index',)

    def __str__(self):
        return '<GroupChild: {}[{}] {}>'.format(self.group, self.index, self.content_object.guid)


class ViewRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    guid = models.CharField(max_length=16)
    date = models.DateTimeField(auto_now_add=True)


class SiteConfig(models.Model):
    name = models.CharField(max_length=128, default="Frog")
    favicon = models.FileField(blank=True, null=True)
    icon = models.ImageField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    enable_likes = models.BooleanField(default=True)
    default_gallery = models.ForeignKey(Gallery, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.id)
    
    def json(self):
        return {
            'name': self.name,
            'favicon': self.favicon.url if self.favicon else None,
            'icon': self.icon.url if self.icon else None,
            'link': self.link,
            'enable_likes': self.enable_likes,
            'default_gallery': self.default_gallery.id if self.default_gallery else 1,
        }
    
    @staticmethod
    def getSiteConfig():
        return SiteConfig.objects.get_or_create(pk=1)[0]
