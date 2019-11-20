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

import os
import json
import time

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.http.request import RawPostDataException
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from path import Path
import psd_tools

from frog.models import (
    Image,
    Video,
    Tag,
    Piece,
    cropBox,
    pilImage,
    Group,
    Gallery,
    SiteConfig,
    FROG_SITE_URL,
    FROG_THUMB_SIZE
)
from frog.models import ViewRecord
from frog.common import Result, getObjectsFromGuids, getRoot, getUser
from frog.uploader import handle_uploaded_file


@require_http_methods(["POST", "PUT", "DELETE"])
def image(request, obj_id):
    """Handles a request based on method and calls the appropriate function"""
    obj = Image.objects.get(pk=obj_id)
    if request.method == "POST":
        return post(request, obj)
    elif request.method == "PUT":
        return put(request, obj)
    elif request.method == "DELETE":
        return delete(request, obj)


@require_http_methods(["POST", "PUT", "DELETE"])
def video(request, obj_id):
    """Handles a request based on method and calls the appropriate function"""
    obj = Video.objects.get(pk=obj_id)
    if request.method == "POST":
        return post(request, obj)
    elif request.method == "PUT":
        return put(request, obj)
    elif request.method == "DELETE":
        return delete(request, obj)


@login_required
@csrf_exempt
def data(request, guid):
    obj = Piece.fromGuid(guid)
    if request.method == "GET":
        res = Result()
        res.append(obj.json())

        return JsonResponse(res.asDict())
    elif request.method == "POST":
        return post(request, obj)
    elif request.method == "PUT":
        return put(request, obj)
    elif request.method == "DELETE":
        return delete(request, obj)


@login_required
def getGuids(request):
    res = Result()

    guids = request.GET.get("guids", "").split(",")
    for _ in getObjectsFromGuids(guids):
        res.append(_.json())

    return JsonResponse(res.asDict())


@login_required
@csrf_exempt
def like(request, guid):
    obj = Piece.fromGuid(guid)
    res = Result()
    if obj.like(request):
        emailLike(request, obj)
    else:
        res.message = 'Cannot "like" things more than once'

    res.append(obj.json())

    return JsonResponse(res.asDict())


@login_required
def post(request, obj):
    try:
        data = request.POST or json.loads(request.body)["body"]
    except RawPostDataException:
        data = request.POST
    tags = data.get("tags", "").split(",")
    resetthumbnail = data.get("reset-thumbnail", False)
    crop = data.get("crop")
    res = Result()

    for tag in tags:
        try:
            t = Tag.objects.get(pk=int(tag))
        except ValueError:
            t, created = Tag.objects.get_or_create(name=tag)
            if created:
                res.append(t.json())
        obj.tags.add(t)

    if obj.custom_thumbnail and (crop or request.FILES or resetthumbnail):
        try:
            os.unlink(getRoot() / obj.custom_thumbnail.name)
        except OSError:
            pass

    if crop:
        box = [int(_) for _ in crop]
        # -- Handle thumbnail upload
        source = Path(obj.source.name)
        relativedest = obj.getPath(True) / "{:.0f}{}".format(
            time.time(), source.ext
        )
        dest = getRoot() / relativedest
        source = getRoot() / source
        if not dest.parent.exists():
            dest.parent.makedirs()
        source.copy(dest)
        obj.custom_thumbnail = relativedest

        image = pilImage.open(dest)

        # Crop from center
        image = image.crop(box)
        image.load()
        # Resize
        image.thumbnail(
            (FROG_THUMB_SIZE, FROG_THUMB_SIZE), pilImage.ANTIALIAS
        )
        image.save(dest)

        obj.save()

    if request.FILES:
        # -- Handle thumbnail upload
        f = request.FILES.get("file")
        relativedest = obj.getPath(True) / f.name
        dest = getRoot() / relativedest
        handle_uploaded_file(dest, f)
        obj.custom_thumbnail = relativedest

        try:
            if dest.ext == ".psd":
                image = psd_tools.PSDLoad(dest).as_PIL()
            else:
                image = pilImage.open(dest)
        except IOError as err:
            res.isError = True
            res.message = "{} is not a supported thumbnail image type".format(
                f.name
            )
            return JsonResponse(res.asDict())

        box, width, height = cropBox(*image.size)
        # Resize
        image.thumbnail((width, height), pilImage.ANTIALIAS)
        # Crop from center
        box = cropBox(*image.size)[0]
        image.crop(box).save(dest)

        obj.save()

    if resetthumbnail:
        obj.custom_thumbnail = None
        obj.save()

    res.value = obj.json()

    return JsonResponse(res.asDict())


@login_required
def put(request, obj):
    for key, value in json.loads(request.body)["body"].items():
        if hasattr(obj, key):
            setattr(obj, key, value)

    obj.save()

    res = Result()
    res.append(obj.json())

    return JsonResponse(res.asDict())


@login_required
def delete(request, obj):
    obj.deleted = True
    obj.save()
    res = Result()
    res.append(obj.json())

    return JsonResponse(res.asDict())


def group(request, obj_id=None):
    res = Result()

    if request.method == "GET":
        try:
            group = Group.objects.get(pk=obj_id)
            res.append(group.json())
        except ObjectDoesNotExist as err:
            res.isError = True
            res.message = str(err)
    elif request.method == "POST":
        data = json.loads(request.body)["body"]
        user = getUser(request)
        if user:
            items = getObjectsFromGuids(data["guids"])
            gallery = data.get("gallery")
            g = Group()
            g.author = user
            g.title = data.get("title", items[0].title)
            g.thumbnail = items[0].thumbnail
            g.description = data.get("description", items[0].description)
            g.save()
            g.guid = g.getGuid().guid
            g.save()

            if gallery:
                Gallery.objects.get(pk=gallery).groups.add(g)

            for item in items:
                g.appendChild(item)
            res.append(g.json())
        else:
            res.isError = True
            res.message = "No user found to create group"
    elif request.method == "PUT":
        data = json.loads(request.body)["body"]
        g = Group.objects.get(pk=obj_id)
        action = data["action"]
        index = data.get("index")
        item = Piece.fromGuid(data["guid"])
        if action == "append":
            g.appendChild(item)
        elif action == "insert":
            g.insertChild(index, item)
        else:
            g.removeChild(item)
        res.append(g.json())
    else:
        g = Group.objects.get(pk=obj_id)
        g.delete()

    return JsonResponse(res.asDict())


@require_http_methods(["POST"])
@login_required
def recordView(request):
    res = Result()
    data = json.loads(request.body)["body"]

    item = getObjectsFromGuids([data["guid"]])
    if item:
        item = item[0]

        created = ViewRecord.objects.get_or_create(
            user=request.user, guid=data["guid"]
        )[1]
        if created:
            item.view_count += 1
            item.save()

        res.append(item.view_count)
    else:
        res.isError = True
        res.message = "No object foudn for guid {}".format(data["guid"])

    return JsonResponse(res.asDict())


def emailLike(request, obj):
    if not obj.author.frog_prefs.get_or_create()[0].json()["emailLikes"]:
        return

    if obj.author == request.user:
        return

    config = SiteConfig.getSiteConfig()
    html = render_to_string(
        "frog/comment_email.html",
        {
            "user": request.user,
            "object": obj,
            "comment": "",
            "action_type": "liked",
            "image": isinstance(obj, Image),
            "SITE_URL": FROG_SITE_URL,
        },
    )
    subject = "{}: {} liked {}".format(
        config.name, request.user.username, obj.title
    )
    fromemail = request.user.email
    to = obj.author.email
    text_content = "This is an important message."
    html_content = html

    send_mail(subject, text_content, fromemail, [to], html_message=html_content)
