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

from __future__ import division

import os
import random
import string
import hashlib
import imp

from django.contrib.auth.models import User

try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    import ujson as json
except ImportError:
    import json

from django.conf import settings

import path
import PIL.Image
import psd_tools

from frog.models import Image, Video, Group, Marmoset, SiteConfig


class Result(object):
    """Standardized result for ajax requests"""

    def __init__(self):
        self.message = ""
        self.value = None
        self.values = []
        self.isError = False

    @property
    def isSuccess(self):
        return not self.isError

    def append(self, val):
        """Appends the object to the end of the values list.  Will also set the value to the first
        item in the values list

        :param val: Object to append
        :type val: primitive
        """
        self.values.append(val)
        self.value = self.values[0]

    def asDict(self):
        """Returns a serializable object"""
        return {
            "isError": self.isError,
            "message": self.message,
            "values": self.values,
            "value": self.value,
        }


def userToJson(user):
    """Returns a serializable User dict

    :param user: User to get info for
    :type user: User
    :returns: dict
    """
    obj = {
        "id": user.id,
        "username": user.username,
        "name": user.get_full_name(),
        "email": user.email,
    }

    return obj


def commentToJson(comment):
    """Returns a serializable Comment dict

    :param comment: Comment to get info for
    :type comment: Comment
    :returns: dict
    """
    obj = {
        "id": comment.id,
        "comment": comment.comment,
        "user": userToJson(comment.user),
        "date": comment.submit_date.isoformat(),
    }

    return obj


def getPutData(request):
    """Adds raw post to the PUT and DELETE querydicts on the request so they behave like post

    :param request: Request object to add PUT/DELETE to
    :type request: Request
    """
    dataDict = {}
    data = request.body

    for n in urlparse.parse_qsl(data):
        dataDict[n[0]] = n[1]

    setattr(request, "PUT", dataDict)
    setattr(request, "DELETE", dataDict)


def getHashForFile(f):
    """Returns a hash value for a file

    :param f: File to hash
    :type f: str
    :returns: str
    """
    hashVal = hashlib.sha1()
    while True:
        r = f.read(1024)
        if not r:
            break
        hashVal.update(r)
    f.seek(0)

    return hashVal.hexdigest()


def getRoot():
    """Convenience to return the media root with forward slashes"""
    return path.Path(settings.MEDIA_ROOT.replace("\\", "/"))


def uniqueID(size=6, chars=string.ascii_uppercase + string.digits):
    """A quick and dirty way to get a unique string"""
    return "".join(random.choice(chars) for x in range(size))


def getObjectsFromGuids(guids):
    """Gets the model objects based on a guid list

    :param guids: Guids to get objects for
    :type guids: list
    :returns: list
    """
    guids = guids[:]
    img = list(Image.objects.filter(guid__in=guids))
    vid = list(Video.objects.filter(guid__in=guids))
    grp = list(Group.objects.filter(guid__in=guids))
    marmosets = list(Marmoset.objects.filter(guid__in=guids))
    objects = img + vid + grp + marmosets
    sortedobjects = []

    if objects:
        while guids:
            for obj in iter(objects):
                if obj.guid == guids[0]:
                    sortedobjects.append(obj)
                    guids.pop(0)
                    break

    return sortedobjects


def getClientIP(request):
    """Returns the best IP address found from the request"""
    forwardedfor = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwardedfor:
        ip = forwardedfor.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip


def cropCenter(image, width, height):
    """Resizes and crops the center of an image to fit width and height"""
    image = image.copy()
    size = max(width, height)
    sourceratio = image.size[0] / image.size[1]
    targetratio = width / height

    # Scale
    scaledratio = width / image.size[0]
    if (sourceratio >= 1.0 and targetratio >= 1.0) or (
        sourceratio < 1.0 and targetratio >= 1.0
    ):
        h = image.size[1] * scaledratio
        w = width
    else:
        scaledratio = height / image.size[1]
        w = image.size[0] * scaledratio
        h = height

    image = image.resize((int(w), int(h)), PIL.Image.BILINEAR)

    # Crop
    ratio = float(width) / float(height)
    if ratio >= 1.0:
        pad = image.size[1] - height
        clip = int(pad / 2)
        box = (
            0,
            clip if pad % 2 == 0 else clip + 1,
            size,
            image.size[1] - clip,
        )
    else:
        pad = image.size[0] - width
        clip = int(pad / 2)
        box = (
            clip if pad % 2 == 0 else clip + 1,
            0,
            image.size[0] - clip,
            size,
        )

    cropped = image.crop(box)
    cropped.load()

    return cropped


def getUser(request):
    data = json.loads(request.body)["body"]
    username = data.get("user")
    if username:
        user = User.objects.get_or_create(username=username)[0]
    else:
        user = request.user

    if user.is_anonymous():
        user = None

    return user


def saveAsPng(filepath, move=True):
    filepath = path.Path(filepath)
    if filepath.ext == ".png":
        return filepath

    dest = filepath.parent / "{}.png".format(filepath.namebase)
    if filepath.ext == ".psd":
        image = psd_tools.PSDImage.load(filepath).as_PIL()
    else:
        image = PIL.Image.open(filepath)

    image.save(dest)

    if move:
        os.remove(filepath)

    return dest
