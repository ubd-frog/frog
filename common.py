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

import sys
import time
import datetime
import urlparse
import collections
import random
import string
import hashlib
import imp

try:
    import ujson as json
except ImportError:
    import json

from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from frog.models import Image, Video
from frog.plugin import FrogPluginRegistry

from path import path as Path


def userToJson(user, context=None, **kwargs):
    obj = {
        'id': user.id,
        'username': user.username,
        'name': user.get_full_name(),
        'email': user.email,
    }

    return obj

def JsonResponse(obj=None, status=200):
    obj = obj or {}
    try:
        data = json.dumps(obj, indent=4)
    except TypeError:
        data = json.dumps(obj.__dict__, indent=4)
    return HttpResponse(data, mimetype='application/json', status=status)


class MainView(object):

    def __init__(self, model=None):
        if model:
            self.model = model
            self._ctype = ContentType.objects.get_for_model(self.model)
            self.template = '%s/%s.html' % (self._ctype.app_label, self._ctype.model)
        self.context = {}

    def _processRequest(self, request, obj_id=None):
        obj = {'request': request, 'context': {}}
        try:
            self.id = int(obj_id)
            obj['id'] = int(obj_id)
        except TypeError:
            pass

        dataDict = {}
        for n in urlparse.parse_qsl(request.raw_post_data):
            dataDict[n[0]] = n[1]
        obj['DELETE'] = obj['PUT'] = dataDict

        if obj_id:
            obj['object'] = self.model.objects.get(pk=obj_id)
            obj['context']['object'] = obj['object']
            obj['context']['obj'] = None if not obj['object'] or isinstance(obj['object'], User) else json.dumps(obj['object'].json())
            try:
                obj['context']['title'] = obj['object'].name
            except AttributeError:
                pass
        
        obj['context']['ajax'] = request.is_ajax()

        return obj

    def _getData(self, request):
        dataDict = {}
        for n in urlparse.parse_qsl(request.raw_post_data):
            dataDict[n[0]] = n[1]
        
        return dataDict

    def _getObject(self, id):
        try:
            obj = self.model.objects.get(pk=id)

            return obj
        except ObjectDoesNotExist:
            raise Http404
    
    @csrf_exempt
    def index(self, request, *args, **kwargs):
        if kwargs.has_key('obj_id'):
            return self.view(request, kwargs['obj_id'])
        else:
            if request.method == 'GET':
                return self.get(request)
            elif request.method == 'POST':
                return self.post(request)
            elif request.method == 'PUT':
                setattr(request, 'PUT', self._getData(request))
                return self.put(request)
            elif request.method == 'DELETE':
                setattr(request, 'DELETE', self._getData(request))
                return self.delete(request)

    @csrf_exempt
    def view(self, request, obj_id=None):
        if request.method == 'GET':
            if request.GET.get('json', False):
                res = Result()
                res.isSuccess = True
                res.append(self.object.json())

                return JsonResponse(res)
            return self.get(request, obj_id)
        elif request.method == 'POST':
            return self.post(request, obj_id)
        elif request.method == 'PUT':
            setattr(request, 'PUT', self._getData(request))
            return self.put(request, obj_id)
        elif request.method == 'DELETE':
            setattr(request, 'DELETE', self._getData(request))
            return self.delete(request, obj_id)
    
    def get(self, request, *args, **kwargs):
        obj = self._getObject(args[0])
        return self.render(request, {'object': obj})
    
    def post(self, request, *args, **kwargs):
        return HttpResponse()
    
    def put(self, request, *args, **kwargs):
        return HttpResponse()
    
    def delete(self, request, *args, **kwargs):
        return HttpResponse()

    def render(self, request, context):
        return render(request, self.template, context)


class Result(object):
    def __init__(self):
        self.message = ''
        self.value = None
        self.values = []
        self.isError = False
        self.isSuccess = False

    def append(self, val):
        self.values.append(val)
        self.value = self.values[0]


def getRoot():
    return Path(settings.MEDIA_ROOT.replace('\\', '/'))

def getHashForFile(f):
    hashVal = hashlib.sha1()
    while True:
        r = f.read(1024)
        if not r:
            break
        hashVal.update(r)
    f.seek(0)

    return hashVal.hexdigest()

def uniqueID(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in xrange(size))

def getObjectsFromGuids(guids):
    img = list(Image.objects.filter(guid__in=guids))
    vid = list(Video.objects.filter(guid__in=guids))
    objects = img + vid

    return objects

def commentToJson(comment):
    obj = {
        'id': comment.id,
        'comment': comment.comment,
        'user': userToJson(comment.user),
        'date': comment.submit_date.isoformat(),
    }

    return obj

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
    # ROOT = Path(sys.path[0])
    # for pyfile in ROOT.walk('frog_plugin.py'):
    #     file_, path, descr = imp.find_module(pyfile.namebase, [pyfile.parent])
    #     if file_:
    #         imp.load_module(pyfile.namebase, file_, path, descr)
    for app in settings.INSTALLED_APPS:
        if not app.startswith('django'):
            module = __import__(app)
            moduledir = Path(module.__file__).parent
            plugin = moduledir / 'frog_plugin.py'
            if plugin.exists():
                file_, path, desc = imp.find_module('frog_plugin', [moduledir])
                if file_:
                    imp.load_module('frog_plugin', file_, path, desc)

    return FrogPluginRegistry.plugins

PluginContext = getPluginContext()