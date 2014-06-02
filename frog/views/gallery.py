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
Gallery API

::

    GET     /        Lists the galleries currently visible by the current user
    POST    /        Creates a gallery object
    GET     /id      Gallery object if visible by the current user
    PUT     /id      Adds image or video objects to the gallery
    DELETE  /id      Removes image or video objects from the gallery
    GET     /filter  Returns a filtered list of image and video objects
"""

import time

try:
    import ujson as json
except ImportError:
    import json

from django.http import HttpResponseRedirect
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.contrib.auth.decorators import login_required

try:
    from haystack.query import SearchQuerySet
    HAYSTACK = True
except (ImportError, ImproperlyConfigured):
    HAYSTACK = False

from frog.views import LOGGER
from frog.models import Gallery, Image, Video, UserPref
from frog.common import Result, JsonResponse, getObjectsFromGuids, getPutData


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
    if obj_id:
        obj = Gallery.objects.get(pk=obj_id)
        if obj.security != Gallery.PUBLIC and request.user.is_anonymous():
            return HttpResponseRedirect('frogaccess_denied')

        return render(request, 'frog/gallery.html', {'object': obj})
    else:
        res = Result()
        res.isSuccess = True
        flat = bool(request.GET.get('flat'))
        if request.user.is_anonymous():
            objects = Gallery.objects.filter(security=Gallery.PUBLIC)
        else:
            objects = Gallery.objects.filter(Q(security__lt=Gallery.PRIVATE) | Q(owner=request.user))

        objects = objects.filter(parent__isnull=True)

        for n in objects:
            if flat:
                res.append({'title': n.title, 'id': n.id});
                for child in n.gallery_set.all().order_by('title'):
                    res.append({'title': '-- %s' % child.title, 'id': child.id});
            else:
                res.append(n.json())

        return JsonResponse(res)

@login_required
def post(request):
    """ Create a Gallery """
    defaultname = 'New Gallery %i' % Gallery.objects.all().count()
    title = request.POST.get('title', defaultname)
    description = request.POST.get('description', '')
    security = int(request.POST.get('security', Gallery.PUBLIC))
    parentid = request.POST.get('parent')
    if parentid:
        parent = Gallery.objects.get(pk=int(parentid))
        g, created = parent.gallery_set.get_or_create(title=title)
        g.security = parent.security
    else:
        g, created = Gallery.objects.get_or_create(title=title)
        g.security = security

    g.description = description
    g.owner = request.user
    g.save()

    res = Result()
    res.isSuccess = True
    res.append(g.json())
    res.message = 'Gallery created' if created else ''

    return JsonResponse(res)

@login_required
def put(request, obj_id=None):
    """ Adds Image and Video objects to Gallery based on GUIDs """
    guids = filter(None, request.PUT.get('guids', '').split(','))
    security = request.PUT.get('security')
    object_ = Gallery.objects.get(pk=obj_id)
    
    if guids:
        objects = getObjectsFromGuids(guids)

        images = filter(lambda x: isinstance(x, Image), objects)
        videos = filter(lambda x: isinstance(x, Video), objects)

        object_.images.add(*images)
        object_.videos.add(*videos)
    
    if security is not None:
        object_.security = json.loads(security)
        object_.save()
        for child in object_.gallery_set.all():
            child.security = object_.security
            child.save()

    res = Result()
    res.append(object_.json())
    res.isSuccess = True

    return JsonResponse(res)

@login_required
def delete(request, obj_id=None):
    """ Removes ImageVideo objects from Gallery """
    guids = request.DELETE.get('guids', '').split(',')
    objects = getObjectsFromGuids(guids)
    object_ = Gallery.objects.get(pk=obj_id)

    for o in objects:
        if isinstance(o, Image):
            object_.images.remove(o)
        elif isinstance(o, Video):
            object_.videos.remove(o)

    res = Result()
    res.isSuccess = True

    return JsonResponse(res)

def filterObjects(request, obj_id):
    """
    Filters Gallery for the requested ImageVideo objects.  Returns a Result object with 
    serialized objects
    """
    print obj_id
    obj = Gallery.objects.get(pk=obj_id)

    if request.user.is_anonymous() and obj.security != Gallery.PUBLIC:
        res = Result()
        res.isError = True
        res.message = 'This gallery is not public'

        return JsonResponse(res)

    
    tags = json.loads(request.GET.get('filters', '[[]]'))
    rng = request.GET.get('rng', None)
    more = json.loads(request.GET.get('more', 'false'))
    models = request.GET.get('models', 'image,video')
    if models == '':
        models = 'image,video'

    tags = filter(None, tags)

    models = [ContentType.objects.get(app_label='frog', model=x) for x in models.split(',')]

    return _filter(request, obj, tags=tags, rng=rng, models=models, more=more)

def _filter(request, object_, tags=None, models=(Image, Video), rng=None, more=False):
    """Filters Piece objects from self based on filters, search, and range

    :param tags: List of tag IDs to filter
    :type tags: list
    :param models: List of model classes to filter on
    :type models: list
    :param rng: Range of objects to return. i.e. 0:100
    :type rng: str
    :param more -- bool, Returns more of the same filtered set of images based on session range

    return list, Objects filtered
    """
    
    NOW = time.clock()

    res = Result()
    
    idDict = {}
    objDict = {}
    lastIDs = {}
    data = {}

    LOGGER.debug('init: %f' % (time.clock() - NOW))
    if request.user.is_anonymous():
        gRange = 300
    else:
        Prefs = json.loads(UserPref.objects.get(user=request.user).data)
        gRange = Prefs['batchSize']
    request.session.setdefault('frog_range', '0:%i' % gRange)

    if rng:
        s, e = [int(x) for x in rng.split(':')]
    else:
        if more:
            s = int(request.session.get('frog_range', '0:%i' % gRange).split(':')[1])
            e = s + gRange
            s, e = 0, gRange
        else:
            s, e = 0, gRange

    ## -- Gat all IDs for each model
    for m in models:
        indexes = list(m.model_class().objects.all().values_list('id', flat=True))
        if not indexes:
            continue

        lastIndex = indexes[0]
        if more:
            ## -- This is a request for more results
            idx = request.session.get('last_%s_id' % m.model, lastIndex + 1)
            lastIDs.setdefault('last_%s_id' % m.model, idx)
        else:
            lastIDs['last_%s_id' % m.model] = lastIndex + 1
        
        ## -- Start with objects within range
        idDict[m.model] = m.model_class().objects.filter(gallery=object_, id__lt=lastIDs['last_%s_id' % m.model])
        LOGGER.debug(m.model + '_initial_query: %f' % (time.clock() - NOW))

        if tags:
            for bucket in tags:
                searchQuery = ""
                o = None
                for item in bucket:
                    ## -- filter by tag
                    if isinstance(item, int) or isinstance(item, long):
                        if not o:
                            o = Q()
                        o |= Q(tags__id=item)
                    ## -- add to search string
                    else:
                        searchQuery += item + ' '
                        if not HAYSTACK:
                            if not o:
                                o = Q()
                            ## -- use a basic search
                            LOGGER.debug('search From LIKE')
                            o |= Q(title__icontains=item)
                if HAYSTACK and searchQuery != "":
                    ## -- once all tags have been filtered, filter by search
                    searchIDs = search(searchQuery, m.model_class())
                    if searchIDs:
                        if not o:
                            o = Q()
                        LOGGER.debug('searchFrom haystack:' + str(searchIDs))
                        o |= Q(id__in=searchIDs)

                if o:
                    ## -- apply the filters
                    idDict[m.model] = idDict[m.model].filter(o)
                else:
                    idDict[m.model] = idDict[m.model].none()

            LOGGER.debug(m.model + '_added_buckets(%i): %f' % (len(tags), time.clock() - NOW))
        
        ## -- Get all ids of filtered objects, this will be a very fast query
        idDict[m.model] = list(idDict[m.model].values_list('id', flat=True))
        LOGGER.debug(m.model + '_queried_ids: %f' % (time.clock() - NOW))

        res.message = str(s) + ':' + str(e)
        
        ## -- perform the main query to retrieve the objects we want
        objDict[m.model] = m.model_class().objects.filter(id__in=idDict[m.model]).select_related('author').prefetch_related('tags')
        if not rng:
            objDict[m.model] = objDict[m.model][:gRange]
        objDict[m.model] = list(objDict[m.model])
        LOGGER.debug(m.model + '_queried_obj: %f' % (time.clock() - NOW))
    
    
    ## -- combine and sort all objects by date
    objects = _sortObjects(**objDict) if len(models) > 1 else objDict.values()[0]
    objects = objects[s:e]
    LOGGER.debug('sorted: %f' % (time.clock() - NOW))

    ## -- serialize objects
    for i in objects:
        for m in models:
            if isinstance(i, m.model_class()):
                ## -- set the last ID per model for future lookups
                lastIDs['last_%s_id' % m.model] = i.id
                data['last_%s_id' % m.model] = i.id
        res.append(i.json())
    LOGGER.debug('serialized: %f' % (time.clock() - NOW))

    request.session['frog_range'] = ':'.join((str(s),str(e)))

    LOGGER.debug('total: %f' % (time.clock() - NOW))
    request.session['last_image_id'] = lastIDs.get('last_image_id', 0)
    request.session['last_video_id'] = lastIDs.get('last_video_id', 0)
    
    data['count'] = len(objects)
    data['queries'] = connection.queries

    res.value = data

    res.isSuccess = True

    return JsonResponse(res)

def _sortObjects(**args):
    """Sorts lists of objects and combines them into a single list"""
    o = []
    
    for m in args.values():
        for l in iter(m):
            o.append(l)
    o = list(set(o))
    o.sort(_sortByCreated)

    return o

def _sortByCreated(a, b):
    """Sort function for object by created date then by ID"""
    if a.created < b.created:
        return 1
    elif a.created > b.created:
        return -1
    else:
        if a.id < b.id:
            return 1
        elif a.id > b.id:
            return -1
        else:
            return 0

def search(query, model):
    """ Performs a search query and returns the object ids """
    query = '%s*' % query.strip()
    LOGGER.debug(query)
    sqs = SearchQuerySet()
    sqs = sqs.filter(content=query).models(model)

    return [o.pk for o in sqs]
