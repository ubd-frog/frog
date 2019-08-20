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
import functools
import logging

import requests
from django.core.mail import mail_managers
from django.http import JsonResponse
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db.models import Q, Count
from django.db import connection
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.conf import settings

import six
import json

try:
    from haystack.query import SearchQuerySet

    HAYSTACK = True
except (ImportError, ImproperlyConfigured):
    HAYSTACK = False

from frog.models import (
    Gallery,
    Image,
    Video,
    Group,
    GallerySubscription,
    SiteConfig,
    Piece,
)
from frog.common import Result, getObjectsFromGuids, getPutData, getClientIP

LOGGER = logging.getLogger("frog")
QUERY_MODELS = [
    _
    for _ in ContentType.objects.filter(app_label="frog")
    if issubclass(_.model_class(), Piece)
]
BATCH_LENGTH = 75


def index(request, obj_id=None):
    """Handles a request based on method and calls the appropriate function"""
    if request.method == "GET":
        return get(request, obj_id)
    elif request.method == "POST":
        return post(request)
    elif request.method == "PUT":
        getPutData(request)
        return put(request, obj_id)
    elif request.method == "DELETE":
        getPutData(request)
        return delete(request, obj_id)


def get(request, obj_id=None):
    if obj_id:
        obj = Gallery.objects.get(pk=obj_id)
        if obj.security != Gallery.PUBLIC and request.user.is_anonymous():
            raise PermissionDenied
    else:
        res = Result()

        personal = []
        clearance = Gallery.PUBLIC

        if request.user.is_authenticated():
            personal = Gallery.objects.filter(
                security=Gallery.PERSONAL, owner=request.user
            )
            try:
                clearance = request.user.frog_prefs.first().clearance
            except AttributeError:
                clearance = Gallery.PUBLIC

        # -- Staff members should see everything
        if request.user.is_staff:
            clearance = Gallery.GUARDED

        objects = Gallery.objects.filter(security__lte=clearance)
        ids = []

        for gallery in objects:
            if gallery.security == Gallery.PERSONAL:
                continue
            if gallery.id in ids:
                continue

            ids.append(gallery.id)
            res.append(gallery.json())

        for gallery in personal:
            res.append(gallery.json())

        return JsonResponse(res.asDict())


@login_required
def post(request):
    """ Create a Gallery """
    defaultname = "New Gallery %i" % Gallery.objects.all().count()
    data = request.POST or json.loads(request.body)["body"]
    title = data.get("title", defaultname)
    description = data.get("description", "")
    security = int(
        data.get("security", request.user.frog_prefs.first().clearance)
    )

    g, created = Gallery.objects.get_or_create(title=title)
    g.security = security
    g.description = description
    g.owner = request.user
    g.save()

    res = Result()
    res.append(g.json())
    res.message = "Gallery created" if created else ""

    return JsonResponse(res.asDict())


@login_required
def put(request, obj_id=None):
    """ Adds Image and Video objects to Gallery based on GUIDs """
    data = request.PUT or json.loads(request.body)["body"]
    guids = data.get("guids", "").split(",")
    move = data.get("from")
    security = request.PUT.get("security")
    gallery = Gallery.objects.get(pk=obj_id)

    # -- Set the security first so subsequent securityChecks will get the correct security level
    if security is not None:
        gallery.security = json.loads(security)
        gallery.save()
        for child in gallery.gallery_set.all():
            child.security = gallery.security
            child.save()

    if guids:
        items = getObjectsFromGuids(guids)
        gallery.addItems(items)

        if move:
            fromgallery = Gallery.objects.get(pk=move)
            fromgallery.removeItems(items)

    res = Result()
    res.append(gallery.json())

    return JsonResponse(res.asDict())


@login_required
def delete(request, obj_id=None):
    """ Removes ImageVideo objects from Gallery """
    data = request.DELETE or json.loads(request.body)
    guids = data.get("guids").split(",")
    items = getObjectsFromGuids(guids)
    gallery = Gallery.objects.get(pk=obj_id)

    LOGGER.info(
        "{} removed {} from {}".format(request.user.email, guids, gallery)
    )

    gallery.removeItems(items)

    res = Result()

    return JsonResponse(res.asDict())


@login_required
def filterObjects(request, obj_id):
    """
    Filters Gallery for the requested ImageVideo objects.  Returns a Result object with
    serialized objects
    """
    if int(obj_id) == 0:
        obj = None
    else:
        obj = Gallery.objects.get(pk=obj_id)

    isanonymous = request.user.is_anonymous()

    if isanonymous and obj is None:
        LOGGER.warn(
            "There was an anonymous access attempt from {} to {}".format(
                getClientIP(request), obj
            )
        )
        raise PermissionDenied()

    if isanonymous and obj and obj.security != Gallery.PUBLIC:
        LOGGER.warn(
            "There was an anonymous access attempt from {} to {}".format(
                getClientIP(request), obj
            )
        )
        raise PermissionDenied()

    if obj and obj.security != Gallery.PERSONAL:
        if request.user.frog_prefs.first().clearance < obj.security:
            raise PermissionDenied()

    tags = json.loads(request.GET.get("filters", "[[]]"))
    more = json.loads(request.GET.get("more", "false"))
    orderby = request.GET.get(
        "orderby", request.user.frog_prefs.get().json()["orderby"]
    )

    tags = [t for t in tags if t]

    return _filter(request, obj, tags=tags, more=more, orderby=orderby)


def _filter(request, object_, tags=None, more=False, orderby="created"):
    """Filters Piece objects from self based on filters, search, and range

    :param tags: List of tag IDs to filter
    :type tags: list
    :param more -- bool, Returns more of the same filtered set of images based on session range

    return list, Objects filtered
    """
    res = Result()

    idDict = {}
    objDict = {}
    data = {}
    modelmap = {}

    # -- Get all IDs for each model
    for m in QUERY_MODELS:
        modelmap[m.model_class()] = m.model

        if object_:
            idDict[m.model] = m.model_class().objects.filter(gallery=object_)
        else:
            idDict[m.model] = m.model_class().objects.all()

        if idDict[m.model] is None:
            continue

        if tags:
            for bucket in tags:
                searchQuery = ""
                o = None
                for item in bucket:
                    if item == 0:
                        # -- filter by tagless
                        idDict[m.model].annotate(num_tags=Count("tags"))
                        if not o:
                            o = Q()
                        o |= Q(num_tags__lte=1)
                        break
                    elif isinstance(item, six.integer_types):
                        # -- filter by tag
                        if not o:
                            o = Q()
                        o |= Q(tags__id=item)
                    else:
                        # -- add to search string
                        searchQuery += item + " "
                        if not HAYSTACK:
                            if not o:
                                o = Q()
                            # -- use a basic search
                            o |= Q(title__icontains=item)

                if HAYSTACK and searchQuery != "":
                    # -- once all tags have been filtered, filter by search
                    searchIDs = search(searchQuery, m.model_class())
                    if searchIDs:
                        if not o:
                            o = Q()
                        o |= Q(id__in=searchIDs)

                if o:
                    # -- apply the filters
                    idDict[m.model] = (
                        idDict[m.model]
                        .annotate(num_tags=Count("tags"))
                        .filter(o)
                    )
                else:
                    idDict[m.model] = idDict[m.model].none()

        # Remove hidden items before slicing so we get an accurate count
        idDict[m.model] = idDict[m.model].exclude(hidden=True)

        # -- Get all ids of filtered objects, this will be a very fast query
        idDict[m.model] = list(
            idDict[m.model]
            .order_by("-{}".format(orderby))
            .values_list("id", flat=True)
        )
        lastid = request.session.get("last_{}".format(m.model), 0)
        if not idDict[m.model]:
            continue

        if not more:
            lastid = idDict[m.model][0]

        try:
            index = idDict[m.model].index(lastid)
        except ValueError:
            index = 0

        if more and lastid != 0:
            index += 1
        idDict[m.model] = idDict[m.model][index : index + BATCH_LENGTH]

        # -- perform the main query to retrieve the objects we want
        objDict[m.model] = m.model_class().objects.filter(
            id__in=idDict[m.model]
        )
        objDict[m.model] = (
            objDict[m.model]
            .select_related("author")
            .prefetch_related("tags")
            .order_by("-{}".format(orderby))
        )
        objDict[m.model] = list(objDict[m.model])

    # -- combine and sort all objects by date
    objects = _sortObjects(orderby, **objDict)
    objects = objects[:BATCH_LENGTH]

    # -- Find out last ids
    lastids = {}
    for obj in objects:
        lastids["last_{}".format(modelmap[obj.__class__])] = obj.id

    for key, value in lastids.items():
        request.session[key] = value

    # -- serialize objects
    for i in objects:
        res.append(i.json())

    data["count"] = len(objects)
    if settings.DEBUG:
        data["queries"] = connection.queries

    res.value = data

    return JsonResponse(res.asDict())


def _sortObjects(orderby="created", **kwargs):
    """Sorts lists of objects and combines them into a single list"""
    o = []

    for m in kwargs.values():
        for l in iter(m):
            o.append(l)
    o = list(set(o))
    sortfunc = _sortByCreated if orderby == "created" else _sortByModified
    if six.PY2:
        o.sort(sortfunc)
    else:
        o.sort(key=functools.cmp_to_key(sortfunc))

    return o


def _sortByCreated(a, b):
    """Sort function for object by created date"""
    if a.created < b.created:
        return 1
    elif a.created > b.created:
        return -1
    else:
        return 0


def _sortByModified(a, b):
    """Sort function for object by modified date"""
    if a.modified < b.modified:
        return 1
    elif a.modified > b.modified:
        return -1
    else:
        return 0


def search(query, model):
    """ Performs a search query and returns the object ids """
    query = query.strip()
    LOGGER.debug(query)
    sqs = SearchQuerySet()
    results = sqs.raw_search("{}*".format(query)).models(model)
    if not results:
        results = sqs.raw_search("*{}".format(query)).models(model)
    if not results:
        results = sqs.raw_search("*{}*".format(query)).models(model)

    return [o.pk for o in results]


@require_POST
@login_required
def subscribe(request, obj_id):
    gallery = Gallery.objects.get(pk=obj_id)
    data = request.POST or json.loads(request.body)["body"]
    frequency = data.get("frequency", GallerySubscription.WEEKLY)

    sub, created = GallerySubscription.objects.get_or_create(
        gallery=gallery, user=request.user, frequency=frequency
    )

    if not created:
        # -- it already existed so delete it
        sub.delete()

    return JsonResponse(Result().asDict())
