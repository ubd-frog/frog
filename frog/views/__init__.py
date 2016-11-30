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

import logging
import json

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import mail_managers
from django.conf import settings

from frog.models import Gallery, Image, Video, Tag, Piece, DefaultPrefs
from frog.common import Result, getObjectsFromGuids, userToJson, getBranding
from frog.uploader import upload
from frog.signals import frog_auth_check
from frog.send_file import send_zipfile
from frog.views import comment, gallery, piece, tag, userpref


LOGGER = logging.getLogger('frog')
INDEX_HTML = getattr(settings, 'FROG_INDEX', 'frog/index.html')


@csrf_exempt
def index(request):
    if request.method == 'GET':
        frog_auth_check.send(sender=None, request=request)

        if not request.user.is_anonymous():
            return HttpResponseRedirect('/frog/gallery/1')
        return render(request, INDEX_HTML, getBranding())
    else:
        return upload(request)


@require_http_methods(['POST'])
def login_(request):
    data = request.POST or json.loads(request.body)['body']
    email = data['email'].lower()
    username = email.split('@')[0]
    password = request.POST.get('password')
    result = Result()
    
    if password is None:
        if not email:
            result.message = 'Please enter an email address'
            result.isError = True
        else:
            # -- SimpleAuth
            user = authenticate(
                username=username,
                first_name=request.POST.get('first_name', 'no').lower(),
                last_name=request.POST.get('last_name', 'author').lower(),
                email=email
            )
    else:
        # -- LDAP
        user = authenticate(username=username, password=password)
        
        if user is None:
            result.message = 'Invalid Credentials'
            result.isError = True

        if not user.is_active:
            result.message = 'User account not active'
            result.isError = True
    
    if result.isError:
        if request.is_ajax():
            return JsonResponse(result.asDict())
        else:
            return render(request, INDEX_HTML, result.asDict())

    # -- Create an artist tag for them
    Tag.objects.get_or_create(
        name=user.get_full_name(),
        defaults={'artist': True}
    )

    login(request, user)

    usergallery = Gallery.objects.get_or_create(title=user.username)[0]
    usergallery.owner = user
    usergallery.security = Gallery.PERSONAL
    usergallery.save()

    if request.is_ajax():
        return JsonResponse(result.asDict())

    return HttpResponseRedirect('/frog/gallery/1')


def logout_(request):
    logout(request)

    response = HttpResponseRedirect('/frog')
    response.delete_cookie('sessionid')

    if request.is_ajax():
        return JsonResponse({'value': 1})

    return response


def auth(request):
    response = HttpResponse()
    if request.user.is_anonymous():
        response.status_code = 401

    return response


def accessDenied(request):
    return render(request, 'frog/access_denied.html')


@login_required
def download(request):
    guids = request.GET.get('guids', '').split(',')

    if guids:
        objects = getObjectsFromGuids(guids)
        fileList = {}
        for n in objects:
            files = n.getFiles()
            fileList.setdefault(n.author.username, [])
            for name, file_ in files.iteritems():
                fileList[n.author.username].append([file_, name])

        response = send_zipfile(request, fileList)
        
        return response


@login_required
def switchArtist(request):
    artist = request.POST.get('artist', None)
    guids = request.POST.get('guids', '').split(',')
    res = Result()
    if artist:
        first, last = artist.lower().split(' ')
        author = User.objects.get_or_create(first_name=first, last_name=last, defaults={
            'username': '%s%s' % (first[0], last),
        })[0]
        tag = Tag.objects.get_or_create(name=artist.lower(), defaults={'artist': True})[0]
        objects = getObjectsFromGuids(guids)
        for n in objects:
            n.author = author
            n.tagArtist(tag)

        res.append(userToJson(author))
        res.value['tag'] = Tag.objects.get(name=artist.lower()).id
    else:
        res.isError = True
        res.message = "No artist provided"

    return JsonResponse(res.asDict())


@login_required
def artistLookup(request):
    res = Result()
    query = request.GET.get('query', False)
    if query:
        users = User.objects.filter(first_name__icontains=query.lower())
    else:
        users = User.objects.all()

    for user in users:
        res.append(userToJson(user))

    return JsonResponse(res.values, safe=False)


@login_required
def helpMe(request):
    msg = '{} is in need of assistance:\n\n{}'.format(request.user.email, request.POST.get('message'))
    mail_managers('Frog Help', msg)

    return HttpResponse()


def isUnique(request):
    path = request.GET.get('path', None)
    res = Result()
    if path:
        if request.user.is_anonymous():
            username = request.GET.get('user', 'noauthor')
            user = User.objects.get(username=username)
        else:
            user = request.user
        
        uniqueID = Piece.getUniqueID(path, user)

        img = Image.objects.filter(unique_id=uniqueID)
        vid = Video.objects.filter(unique_id=uniqueID)
        if img:
            res.append(img[0].json())
        elif vid:
            res.append(vid[0].json())
        else:
            res.append(True)
    else:
        res.isError = True
        res.message = "No path provided"

    return JsonResponse(res.asDict())


def getUser(request):
    res = Result()
    data = {}
    if request.user.is_anonymous():
        res.isError = True
        data['prefs'] = DefaultPrefs
    elif request.GET.get('q'):
        return JsonResponse(res.asDict())
    else:
        data['user'] = userToJson(request.user)
        data['user']['isManager'] = any(request.user.groups.filter(name='manager'))
        data['gallery'] = None
        personal = Gallery.objects.filter(owner=request.user, security=Gallery.PERSONAL)
        if personal:
            data['personal_gallery'] = personal[0].json()
        data['prefs'] = request.user.frog_prefs.get_or_create(user=request.user)[0].json()
        galleryid = request.GET.get('gallery')
        if galleryid is not None:
            gallery = Gallery.objects.filter(pk=galleryid, owner=request.user)
            if gallery:
                data['gallery'] = gallery[0].json()

    res.append(data)

    return JsonResponse(res.asDict())


def branding(request):
    res = Result()
    res.append(getBranding())

    return JsonResponse(res.asDict())
