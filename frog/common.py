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

import random
import string
import hashlib
import imp

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

from frog.models import Image, Video, SITE_CONFIG
from frog.plugin import FrogPluginRegistry


class Result(object):
    """Standardized result for ajax requests"""
    def __init__(self):
        self.message = ''
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
            'isError': self.isError,
            'message': self.message,
            'values': self.values,
            'value': self.value,
        }


def getSiteConfig():
    defaults = SITE_CONFIG.copy()
    defaults.update(getattr(settings, 'SITE_CONFIG', {}))

    return defaults


def userToJson(user):
    """Returns a serializable User dict

    :param user: User to get info for
    :type user: User
    :returns: dict
    """
    obj = {
        'id': user.id,
        'username': user.username,
        'name': user.get_full_name(),
        'email': user.email,
    }

    return obj


def commentToJson(comment):
    """Returns a serializable Comment dict

    :param comment: Comment to get info for
    :type comment: Comment
    :returns: dict
    """
    obj = {
        'id': comment.id,
        'comment': comment.comment,
        'user': userToJson(comment.user),
        'date': comment.submit_date.isoformat(),
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

    setattr(request, 'PUT', dataDict)
    setattr(request, 'DELETE', dataDict)


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
    return path.Path(settings.MEDIA_ROOT.replace('\\', '/'))


def uniqueID(size=6, chars=string.ascii_uppercase + string.digits):
    """A quick and dirty way to get a unique string"""
    return ''.join(random.choice(chars) for x in xrange(size))


def getObjectsFromGuids(guids):
    """Gets the model objects based on a guid list

    :param guids: Guids to get objects for
    :type guids: list
    :returns: list
    """
    guids = guids[:]
    img = list(Image.objects.filter(guid__in=guids))
    vid = list(Video.objects.filter(guid__in=guids))
    objects = img + vid
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
    forwardedfor = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwardedfor:
        ip = forwardedfor.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


def getPluginContext():
    plugins = __discoverPlugins()
    js = []
    css = []
    buttons = []
    altclick = None
    defaultdata = {
        'label': '',
        'icon': '/frog/i/photos.png',
        'callback': '',
        'js': [],
        'css': [],
        'altclick': None,
    }

    for plugin in plugins.values():
        plugin = plugin()
        plugindata = plugin.data()

        if plugindata:
            defdict = defaultdata.copy()
            defdict.update(plugindata)

            if defdict['callback']:
                buttons.append([defdict['label'], defdict['icon'], defdict['callback']])
            if defdict['altclick'] and altclick is None:
                altclick = defdict['altclick']

            js += defdict['js']
            css += defdict['css']

    data = {
        'buttons': buttons,
        'altclick': altclick,
        'js': list(set(js)),
        'css': list(set(css)),
    }

    return data


def __discoverPlugins():
    """ Discover the plugin classes contained in Python files, given a
        list of directory names to scan. Return a list of plugin classes.
    """
    for app in settings.INSTALLED_APPS:
        if not app.startswith('django'):
            module = __import__(app)
            moduledir = path.Path(module.__file__).parent
            plugin = moduledir / 'frog_plugin.py'
            if plugin.exists():
                file_, fpath, desc = imp.find_module('frog_plugin', [moduledir])
                if file_:
                    imp.load_module('frog_plugin', file_, fpath, desc)

    return FrogPluginRegistry.plugins

PluginContext = getPluginContext()
