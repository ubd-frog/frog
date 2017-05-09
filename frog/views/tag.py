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
Tag API

::

    GET     /        Lists all tags
    POST    /        Creates a Tag object
    PUT     /        Adds tags to guids
    DELETE  /        Removes tags from guids
    GET     /search  Search tag list
    GET     /manage  Renders a form for adding/removing tags
    POST    /manage  Adds and removes tags from guids and commits data
"""

import json

from django.shortcuts import render, get_object_or_404
from django.db import connection
from django.db.models import Count, Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from frog.models import Tag, Image, Video
from frog.common import Result, getObjectsFromGuids, getPutData


def index(request, obj_id=None):
    """Handles a request based on method and calls the appropriate function"""
    if request.method == 'GET':
        return get(request, obj_id)
    elif request.method == 'POST':
        return post(request)
    elif request.method == 'PUT':
        getPutData(request)
        return put(request, obj_id)
    elif request.method == 'DELETE':
        getPutData(request)
        return delete(request, obj_id)


def get(request, obj_id=None):
    """Lists all tags

    :returns: json
    """
    res = Result()
    if obj_id:
        if obj_id == '0':
            obj = {
                'id': 0,
                'name': 'TAGLESS',
                'artist': False,
            }
        else:
            obj = get_object_or_404(Tag, pk=obj_id).json()

        res.append(obj)
        return JsonResponse(res.asDict())
    else:
        if request.GET.get('count'):
            itags = Tag.objects.all().annotate(icount=Count('image'))
            vtags = Tag.objects.all().annotate(vcount=Count('video'))

            for i, tag in enumerate(itags):
                tag.count = itags[i].icount + vtags[i].vcount
                res.append(tag.json())
        else:
            for tag in Tag.objects.all():
                res.append(tag.json())

        return JsonResponse(res.asDict())


@login_required
def post(request):
    """Creates a tag object

    :param name: Name for tag
    :type name: str
    :returns: json
    """
    res = Result()
    data = request.POST or json.loads(request.body)['body']
    name = data.get('name', None)

    if not name:
        res.isError = True
        res.message = "No name given"

        return JsonResponse(res.asDict())
    
    tag = Tag.objects.get_or_create(name=name.lower())[0]

    res.append(tag.json())

    return JsonResponse(res.asDict())


@login_required
def put(request, obj_id=None):
    """Adds tags from objects resolved from guids

    :param tags: Tags to add
    :type tags: list
    :param guids: Guids to add tags from
    :type guids: list
    :returns: json
    """
    res = Result()
    data = request.PUT or json.loads(request.body)['body']
    if obj_id:
        # -- Edit the tag
        tag = Tag.objects.get(pk=obj_id)
        tag.name = data.get('name', tag.name)
        tag.artist = data.get('artist', tag.artist)
        tag.save()
    else:
        tags = [_ for _ in data.get('tags', '').split(',') if _]
        guids = [_ for _ in data.get('guids', '').split(',') if _]

        _manageTags(tags, guids)

    return JsonResponse(res.asDict())


@login_required
def delete(request, obj_id=None):
    """Removes tags from objects resolved from guids

    :param tags: Tags to remove
    :type tags: list
    :param guids: Guids to remove tags from
    :type guids: list
    :returns: json
    """
    res = Result()

    if obj_id:
        # -- Delete the tag itself
        tag = Tag.objects.get(pk=obj_id)
        guids = []
        images = Image.objects.filter(tags__id=obj_id)
        guids += [_.guid for _ in images]
        videos = Video.objects.filter(tags__id=obj_id)
        guids += [_.guid for _ in videos]
        # -- Remove all tags from objects
        _manageTags([tag.id], guids, add=False)
        # -- Delete old tags
        tag.delete()
    else:
        tags = [_ for _ in request.DELETE.get('tags', '').split(',') if _]
        guids = [_ for _ in request.DELETE.get('guids', '').split(',') if _]

        _manageTags(tags, guids, add=False)

    return JsonResponse(res.asDict())


@login_required
def resolve(request, name):
    res = Result()

    tag = Tag.objects.filter(name__iexact=name)
    if not tag:
        try:
            tag = Tag.objects.filter(Q(id=name))
        except ValueError:
            pass

    if tag:
        res.append(tag[0].json())

    return JsonResponse(res.asDict())


def search(request):
    """
    Search for Tag objects and returns a Result object with a list of searialize Tag
    objects.

    :param search: Append a "Search for" tag
    :type search: bool
    :param zero: Exclude Tags with no items
    :type zero: bool
    :param artist: Exclude artist tags
    :type artist: bool
    :returns: json
    """
    q = request.GET.get('q', '')
    includeSearch = request.GET.get('search', False)
    nonZero = request.GET.get('zero', False)
    excludeArtist = request.GET.get('artist', False)

    if includeSearch:
        l = [{'id': 0, 'name': 'Search for: %s' % q}]
    else:
        l = []

    query = Tag.objects.filter(name__icontains=q)

    if excludeArtist:
        query = query.exclude(artist=True)

    if nonZero:
        l += [t.json() for t in query if t.count() > 0]
    else:
        l += [t.json() for t in query]

    return JsonResponse(l, safe=False)


@login_required
def manage(request):
    if request.method == 'GET':
        guids = request.GET.get('guids', '').split(',')
        guids = [guid for guid in guids if guid]

        objects = getObjectsFromGuids(guids)
        ids = [o.id for o in objects]

        imgtags = list(Tag.objects.filter(image__id__in=ids).exclude(artist=True))
        vidtags = list(Tag.objects.filter(video__id__in=ids).exclude(artist=True))
        tags = list(set(imgtags + vidtags))

        if request.GET.get('json', False):
            res = Result()
            data = {
                'queries': connection.queries,
            }

            res.append(data)

            return JsonResponse(res.asDict())

        return render(request, 'frog/tag_manage.html', {'tags': tags})
    else:
        res = Result()
        data = request.POST or json.loads(request.body)['body']
        add = data.get('add', '').split(',')
        rem = data.get('rem', '').split(',')
        guids = data.get('guids', '').split(',')

        add = [a for a in add if a]
        rem = [r for r in rem if r]
        addList = []

        for t in add:
            try:
                addList.append(int(t))
            except ValueError:
                tag = Tag.objects.get_or_create(name=t.lower())[0]
                tag.save()
                addList.append(tag.id)

        objects = getObjectsFromGuids(guids)
        addTags = Tag.objects.filter(id__in=addList)
        remTags = Tag.objects.filter(id__in=rem)

        for o in objects:
            for a in addTags:
                o.tags.add(a)
            for r in remTags:
                o.tags.remove(r)

            res.append(o.json())

        return JsonResponse(res.asDict())


@login_required()
@require_http_methods(['POST'])
def merge(request, obj_id):
    """Merges multiple tags into a single tag and all related objects are reassigned"""
    res = Result()
    if request.POST:
        tags = json.loads(request.POST['tags'])
    else:
        tags = json.loads(request.body)['body']['tags']

    guids = []
    images = Image.objects.filter(tags__id__in=tags)
    guids += [_.guid for _ in images]
    videos = Video.objects.filter(tags__id__in=tags)
    guids += [_.guid for _ in videos]
    # -- Remove all tags from objects
    _manageTags(tags, guids, add=False)
    # -- Add merged tag to all objects
    _manageTags([obj_id], guids, add=True)
    # -- Delete old tags
    Tag.objects.filter(pk__in=tags).delete()

    return JsonResponse(res.asDict())


def _manageTags(tagList, guids, add=True):
    """ Adds or Removes Guids from Tags """
    objects = getObjectsFromGuids(guids)
    tags = []
    for tag in tagList:
        try:
            t = Tag.objects.get(pk=int(tag))
        except ValueError:
            t = Tag.objects.get_or_create(name=tag.lower())[0]
        tags.append(t)

    if add:
        return _addTags(tags, objects)
    else:
        return _removeTags(tags, objects)


def _addTags(tags, objects):
    """ Adds tags to objects """
    for t in tags:
        for o in objects:
            o.tags.add(t)

    return True


def _removeTags(tags, objects):
    """ Removes tags from objects """
    for t in tags:
        for o in objects:
            o.tags.remove(t)

    return True
