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

"""
API :: Gallery
GET   /  Returns the current users preferences
POST  /  Sets a key in the user prefs to a value
"""

try:
    import ujson as json
except ImportError:
    import json

from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required

from frog.models import UserPref, DefaultPrefs, GallerySubscription
from frog.common import Result


def index(request):
    """Handles a request based on method and calls the appropriate function"""
    if request.method == 'GET':
        return get(request)
    elif request.method == 'POST':
        return post(request)
    return HttpResponse('')


def get(request):
    """Gets the currently logged in users preferences

    :returns: json
    """
    res = Result()
    obj, created = UserPref.objects.get_or_create(user=request.user, defaults={'data': json.dumps(DefaultPrefs.copy())})

    data = obj.json()
    data['subscriptions'] = [_.json() for _ in GallerySubscription.objects.filter(user=request.user)]

    res.append(data)

    return JsonResponse(res.asDict())


@login_required
def post(request):
    """Sets a key to a value on the currently logged in users preferences

    :param key: Key to set
    :type key: str
    :param val: Value to set
    :type val: primitive
    :returns: json
    """
    data = request.POST or json.loads(request.body)['body']
    key = data.get('key', None)
    val = data.get('val', None)
    res = Result()
    if key is not None and val is not None:
        obj, created = UserPref.objects.get_or_create(user=request.user)
        if created:
            obj.data = json.dumps(DefaultPrefs.copy())
            obj.save()
        try:
            val = json.loads(val)
        except (TypeError, ValueError):
            pass
        obj.setKey(key, val)
        obj.save()
        res.append(obj.json())

    return JsonResponse(res.asDict())