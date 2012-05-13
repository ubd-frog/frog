from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from dev.settings import MEDIA_ROOT

from path import path as Path
from PIL import Image as pilImage

gMaxSize = 2560
gSmallSize = 600
gThumbSize = 256

class Tag(models.Model):
    name = models.CharField(max_length=255)
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
            'tags': [tag.json() for tag in self.tags.all()],
            'thumbnail': self.thumbnail.url,
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

        artistTag = Tag.objects.get_or_create(name=self.author.first_name + ' ' + self.author.last_name)[0]
        self.tags.add(artistTag)

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
        pass

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
        }

        return obj


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
    date = models.DateTimeField()
    interval = models.CharField(max_length=6)
    data = models.TextField()
    gallery = models.ForeignKey(Gallery, related_name='rss_storage')