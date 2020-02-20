##################################################################################################
# Copyright (c) 2020 Brett Dixon
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


import json
import pathlib

from django.http import JsonResponse, RawPostDataException
from django.views import View
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required

from frog.common import Result
from frog.models import Badge, Tag
from frog import getRoot
from frog.uploader import handle_uploaded_file


@login_required
@require_http_methods(["GET", "POST", "DELETE"])
def index(request, badge_id=None):
    if request.method == "GET":
        return get(request)
    elif request.method == "POST":
        return post(request)
    elif request.method == "DELETE":
        return delete(request, badge_id)


def get(request):
    res = Result()

    for badge in Badge.objects.all():
        res.append(badge.json())

    return JsonResponse(res.asDict())


@permission_required('frog.change_badge')
def post(request):
    res = Result()

    data = json.loads(request.POST["body"])
    tag = Tag.objects.get(name=data['tag'])
    badge = Badge.objects.get_or_create(tag=tag)[0]

    if request.FILES.get("image"):
        incomingfilename = pathlib.Path(request.FILES["image"].name)
        filename = '{}{}'.format(tag.name, incomingfilename.suffix)
        dest = getRoot() / "badges" / filename
        if not dest.parent.exists():
            dest.parent.makedirs_p()
        handle_uploaded_file(dest, request.FILES["image"])
        badge.image = "badges/{}".format(filename)

    if badge:
        badge.save()

        res.append(badge.json())
    else:
        res.isError = True
        res.message = "No badge found"

    return JsonResponse(res.asDict())


@permission_required('forg.change_badge')
def delete(request, badge_id):
    res = Result()

    badge = Badge.objects.get(pk=badge_id)
    badge.delete()

    return JsonResponse(res.asDict())
