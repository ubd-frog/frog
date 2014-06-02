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
Piece API

::

    GET     /image/id  Returns a rendered page displaying the requested image
    GET     /video/id  Returns a rendered page displaying the requested video
    POST    /image/id  Add tags to an image object
    POST    /video/id  Add tags to an video object
    DELETE  /image/id  Flags the image as deleted in the database
    DELETE  /video/id  Flags the video as deleted in the database
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from frog.models import Image, Video, Tag
from frog.common import Result, JsonResponse, getPutData


def image(request, obj_id):
    """Handles a request based on method and calls the appropriate function"""
    obj = Image.objects.get(pk=obj_id)
    if request.method == 'GET':
        return get(request, obj)
    elif request.method == 'POST':
        return post(request, obj)
    elif request.method == 'DELETE':
        getPutData(request)
        return delete(request, obj)

def video(request, obj_id):
    """Handles a request based on method and calls the appropriate function"""
    obj = Video.objects.get(pk=obj_id)
    if request.method == 'GET':
        return get(request, obj)
    elif request.method == 'POST':
        return post(request, obj)
    elif request.method == 'DELETE':
        getPutData(request)
        return delete(request, obj)

def get(request, obj):
    if isinstance(obj, Image):
        template = 'frog/image.html'
    else:
        template = 'frog/video.html'

    return render(request, template, {'object': obj})

@login_required
def post(self, request, obj):
    tags = request.POST.get('tags', '').split(',')
    res = Result()
    for tag in tags:
        try:
            t = Tag.objects.get(pk=int(tag))
        except ValueError:
            t, created = Tag.objects.get_or_create(name=tag)
            if created:
                res.append(t.json())
        obj.tags.add(t)

    res.isSuccess = True

    return JsonResponse(res)

@login_required
def delete(self, request, obj):
    obj.deleted = True
    obj.save()
    res = Result()
    res.isSuccess = True
    res.value = obj.json()

    return JsonResponse(res)
