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

from django.shortcuts import render, get_object_or_404
from django.db import connection
from django.contrib.auth.decorators import login_required

from frog.models import Tag
from frog.common import Result, JsonResponse, getObjectsFromGuids, getPutData


def index(request, obj_id=None):
    """Handles a request based on method and calls the appropriate function"""
    if request.method == 'GET':
        return get(request, obj_id)
    elif request.method == 'POST':
        return post(request)
    elif request.method == 'PUT':
        getPutData(request)
        return put(request)
    elif request.method == 'DELETE':
        getPutData(request)
        return delete(request)

def get(request, obj_id=None):
    """Lists all tags

    :returns: json
    """
    if obj_id:
        obj = get_object_or_404(Tag, pk=obj_id)

        return render(request, 'frog/tag.html', {'object': obj})
    else:
        res = Result()
        res.isSuccess = True
        for n in Tag.objects.all():
            res.append(n.json())

        return JsonResponse(res)

@login_required
def post(request):
    """Creates a tag object

    :param name: Name for tag
    :type name: str
    :returns: json
    """
    res = Result()
    name = request.POST.get('name', None)

    if not name:
        res.isError = True
        res.message = "No name given"

        return JsonResponse(res)
    
    tag, created = Tag.objects.get_or_create(name=name.lower())

    res.isSuccess = True
    if created:
        res.message = "Created"

    res.append(tag.json())

    return JsonResponse(res)

@login_required
def put(request):
    """Adds tags from objects resolved from guids

    :param tags: Tags to add
    :type tags: list
    :param guids: Guids to add tags from
    :type guids: list
    :returns: json
    """
    tagList = filter(None, request.PUT.get('tags', '').split(','))
    guids = request.PUT.get('guids', '').split(',')
    res = Result()
    res.isSuccess = True

    _manageTags(tagList, guids)

    return JsonResponse(res)

@login_required
def delete(request):
    """Removes tags from objects resolved from guids

    :param tags: Tags to remove
    :type tags: list
    :param guids: Guids to remove tags from
    :type guids: list
    :returns: json
    """
    tagList = filter(None, request.DELETE.get('tags', '').split(','))
    guids = request.DELETE.get('guids', '').split(',')
    res = Result()
    res.isSuccess = True

    _manageTags(tagList, guids, add=False)

    return JsonResponse(res)

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

    return JsonResponse(l)

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

            res.value = data

            res.isSuccess = True

            return JsonResponse(res)

        return render(request, 'frog/tag_manage.html', {'tags': tags})
    else:
        add = request.POST.get('add', '').split(',')
        rem = request.POST.get('rem', '').split(',')
        guids = request.POST.get('guids', '').split(',')

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

        res = Result()
        res.isSuccess = True

        return JsonResponse(res)

def _manageTags(tagList, guids, add=True):
    """ Adds or Removed Guids from Tags """
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