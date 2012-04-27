import time
import datetime
import urlparse
import collections
import random
import string
import hashlib
try:
    import ujson as json
except ImportError:
    import json

from django.http import HttpResponse
from django.shortcuts import render

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

from settings import MEDIA_URL

from frog.models import Image, Video



def userToJson(user, context=None, **kwargs):
    obj = {
        'id': user.id,
        'username': user.username,
        'name': user.first_name + ' ' + user.last_name,
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
        self.context['MEDIA_URL'] = MEDIA_URL

    def _processRequest(self, request, obj_id=None):
        try:
            self.id = int(obj_id)
        except TypeError:
            pass
        
        self.request = request
        self.GET = self.request.GET
        self.POST = self.request.POST
        dataDict = {}
        for n in urlparse.parse_qsl(request.raw_post_data):
            dataDict[n[0]] = n[1]
        self.DELETE = self.PUT = dataDict
        self.user = request.user
        self.object = None
        if obj_id:
            self.object = self.model.objects.get(pk=obj_id)
            self.context['object'] = self.object
            self.context['obj'] = None if not self.object or isinstance(self.object, User) else json.dumps(self.object.json())
            try:
                self.context['title'] = self.object.name
            except AttributeError:
                pass
        
        self.context['ajax'] = request.is_ajax()
    
    @csrf_exempt
    def index(self, request, *args, **kwargs):
        if kwargs.has_key('obj_id'):
            return self.view(request, kwargs['obj_id'])
        else:
            self._processRequest(request)
            if request.method == 'GET':
                return self.get(request)
            elif request.method == 'POST':
                return self.post(request)
            elif request.method == 'PUT':
                return self.put(request)
            elif request.method == 'DELETE':
                return self.delete(request)

    @csrf_exempt
    def view(self, request, obj_id=None):
        self._processRequest(request, obj_id)

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
            return self.put(request, obj_id)
        elif request.method == 'DELETE':
            return self.delete(request, obj_id)
    
    def get(self, request, *args, **kwargs):
        return self.render()
    
    def post(self, request, *args, **kwargs):
        return HttpResponse()
    
    def put(self, request, *args, **kwargs):
        return HttpResponse()
    
    def delete(self, request, *args, **kwargs):
        return HttpResponse()

    def render(self):
        return render(self.request, self.template, self.context)


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


def uniqueID(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in xrange(size))

def getHashForFile(f):
    hashVal = hashlib.sha1()
    while True:
        r = f.read(1024)
        if not r:
            break
        hashVal.update(r)
    f.seek(0)

    return hashVal.hexdigest()

def getObjectsFromGuids(guids):
    img = list(Image.objects.filter(guid__in=guids))
    vid = list(Video.objects.filter(guid__in=guids))
    objects = img + vid

    return objects