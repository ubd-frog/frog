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


import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required

from frog.common import Result
from frog.models import SiteConfig, ROOT, Gallery
from frog.uploader import handle_uploaded_file


@login_required
@permission_required('siteconfig.can_change')
@require_http_methods(["GET", "POST"])
def index(request):
    if request.method == "GET":
        return get(request)
    elif request.method == "POST":
        return post(request)


def get(request):
    res = Result()
    res.append(SiteConfig.getSiteConfig().json())

    return JsonResponse(res.asDict())


def post(request):
    res = Result()
    data = json.loads(request.body)["body"]

    config = SiteConfig.getSiteConfig()
    config.name = data.get("name", config.name)
    if request.FILES.get("favicon"):
        dest = ROOT / "favicon.ico"
        handle_uploaded_file(dest, request.FILES["favicon"])
        config.favicon = "favicon.ico"
    if request.FILES.get("icon"):
        dest = ROOT / request.FILES["icon"].name
        handle_uploaded_file(dest, request.FILES["icon"])
        config.favicon = request.FILES["icon"].name

    config.link = data.get("link", config.link)
    config.enable_likes = data.get("enable_likes", config.enable_likes)
    config.site_url = data.get("site_url", config.site_url)

    if data.get("default_gallery"):
        gallery = Gallery.objects.get(pk=data["default_gallery"])
        config.default_gallery = gallery

    config.save()

    res.append(SiteConfig.getSiteConfig().json())

    return JsonResponse(res.asDict())
