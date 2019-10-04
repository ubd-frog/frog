##################################################################################################
# Copyright (c) 2012 Brett Dixon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##################################################################################################

"""
Comment API

::

    GET     /        Returns a rendered list of comments
    GET     /id      Returns a serialized comment
    POST    /id      Creates a comment for an object
    PUT     /id      Updates the content of the comment
"""

import json

from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from django_comments.models import Comment

from frog.common import Result, commentToJson, getObjectsFromGuids
from frog.models import Image, Video, Group, Marmoset, SiteConfig, FROG_SITE_URL


def index(request, obj_id):
    """Handles a request based on method and calls the appropriate function"""
    if request.method == "GET":
        return get(request, obj_id)
    elif request.method == "PUT":
        return put(request, obj_id)


def get(request, obj_id):
    """Returns a serialized object
    :param obj_id: ID of comment object
    :type obj_id: int
    :returns: json
    """
    res = Result()
    c = Comment.objects.get(pk=obj_id)
    res.append(commentToJson(c))

    return JsonResponse(res.asDict())


@login_required
def post(request):
    """Returns a serialized object"""
    data = json.loads(request.body)["body"]
    guid = data.get("guid", None)
    res = Result()

    if guid:
        obj = getObjectsFromGuids([guid])[0]
        comment = Comment()
        comment.comment = data.get("comment", "No comment")
        comment.user = request.user
        comment.user_name = request.user.get_full_name()
        comment.user_email = request.user.email
        comment.content_object = obj
        # For our purposes, we never have more than one site
        comment.site_id = 1
        comment.save()

        obj.comment_count += 1
        obj.save()

        emailComment(comment, obj, request)

        res.append(commentToJson(comment))

    return JsonResponse(res.asDict())


@login_required
def put(request, obj_id):
    """Updates the content of a comment
    :param obj_id: ID of comment object
    :type obj_id: int
    :returns: json
    """
    res = Result()
    c = Comment.objects.get(pk=obj_id)
    data = json.loads(request.body)["body"]
    content = data.get("comment", None)
    if content:
        c.comment = content
        c.save()

        res.append(commentToJson(c))

    return JsonResponse(res.asDict())


@csrf_exempt
def commentList(request):
    """Returns a rendered list of comments
    :returns: html
    """
    if request.method == "POST":
        return post(request)

    res = Result()
    comments = []
    guid = request.GET.get("guid", None)

    if guid:
        obj = getObjectsFromGuids([guid])
        if obj:
            obj = obj[0]

            if obj.AssetType == Image.AssetType:
                model = "image"
            elif obj.AssetType == Video.AssetType:
                model = "video"
            elif obj.AssetType == Group.AssetType:
                model = "group"
            elif obj.AssetType == Marmoset.AssetType:
                model = "marmoset"
            else:
                model = None

            if model:
                contenttype = ContentType.objects.get(
                    app_label="frog", model=model
                )
                comments = Comment.objects.filter(
                    object_pk=obj.id, content_type=contenttype
                )
        else:
            res.isError = True
            res.message = "Invalid object, could not lookup comments for {}".format(
                guid
            )

    for comment in comments:
        res.append(commentToJson(comment))
    return JsonResponse(res.asDict())


def emailComment(comment, obj, request):
    """Send an email to the author about a new comment"""
    if not obj.author.frog_prefs.get().json()["emailComments"]:
        return

    if obj.author == request.user:
        return

    config = SiteConfig.getSiteConfig()

    html = render_to_string(
        "frog/comment_email.html",
        {
            "user": comment.user,
            "comment": comment.comment,
            "object": obj,
            "action_type": "commented on",
            "image": isinstance(obj, Image),
            "SITE_URL": FROG_SITE_URL,
        },
    )

    subject = "{}: Comment from {}".format(config.name, comment.user_name)
    fromemail = comment.user_email
    to = obj.author.email
    text_content = "This is an important message."
    html_content = html

    send_mail(subject, text_content, fromemail, [to], html_message=html_content)
