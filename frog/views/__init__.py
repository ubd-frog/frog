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

import datetime
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.core.mail import mail_admins
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from frog.models import Gallery, Image, Video, Tag, Piece, DefaultPrefs, ReleaseNotes
from frog.common import Result, getObjectsFromGuids, userToJson, getSiteConfig
from frog.uploader import upload
from frog.send_file import send_zipfile
from frog.views import comment, gallery, piece, tag, userpref


LOGGER = logging.getLogger('frog')


@csrf_exempt
@ensure_csrf_cookie
@require_http_methods(['POST'])
def index(request):
    return upload(request)


@require_http_methods(['GET', 'POST'])
def login_(request):
    data = request.POST or json.loads(request.body)['body']
    email = data['email'].lower()
    password = data.get('password')
    result = Result()
    user = None

    if email:
        user = authenticate(username=email, password=password)
    else:
        result.message = 'Please enter an email address'
        result.isError = True

    if user:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        if not user.is_active:
            result.message = 'User account not active'
            result.isError = True
    else:
        result.message = 'Invalid Credentials'
        result.isError = True

    if result.isError:
        return JsonResponse(result.asDict())

    login(request, user)

    # -- Create an artist tag for them
    Tag.objects.get_or_create(
        name=user.get_full_name(),
        defaults={'artist': True}
    )

    return JsonResponse(result.asDict())


def logout_(request):
    logout(request)

    response = HttpResponseRedirect('/frog')
    response.delete_cookie('sessionid')

    return JsonResponse({'value': 1})


def auth(request):
    response = HttpResponse()
    if request.user.is_anonymous():
        LOGGER.warn('Unauthorized static lookup attempt', extra={'request': request})
        response.status_code = 401

    return response


def accessDenied(request):
    LOGGER.warn('Access Denied', extra={'request': request})
    return render(request, 'frog/access_denied.html')


@login_required
def download(request):
    guids = request.GET.get('guids', '').split(',')

    if guids:
        LOGGER.info('{} downloaded {}'.format(request.user.email, guids))
        objects = getObjectsFromGuids(guids)
        filelist = {}
        for n in objects:
            files = n.getFiles()
            filelist.setdefault(n.author.username, [])
            for name, file_ in files.iteritems():
                filelist[n.author.username].append([file_, name])

        response = send_zipfile(request, filelist)
        
        return response


@login_required
@require_http_methods(['POST'])
def switchArtist(request):
    data = request.POST or json.loads(request.body)['body']
    artist = data.get('artist', None)
    guids = data.get('guids', '').split(',')

    res = Result()
    if artist:
        if isinstance(artist, int):
            author = User.objects.get(pk=artist)
            tag = Tag.objects.get_or_create(name=author.get_full_name().lower(), defaults={'artist': True})[0]
        else:
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
        res.value['tag'] = tag.id

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
@require_http_methods(['POST'])
def isUnique(request):
    data = request.POST or json.loads(request.body)['body']
    paths = data.get('paths', [])
    res = Result()

    if data.get('user'):
        user = User.objects.get(username=data['user'])
    elif request.user.is_anonymous():
        raise HttpResponseForbidden
    else:
        user = request.user

    for path in paths:
        uniqueid = Piece.getUniqueID(path, user)

        img = Image.objects.filter(unique_id=uniqueid)
        vid = Video.objects.filter(unique_id=uniqueid)
        if img:
            res.append(img[0].json())
        elif vid:
            res.append(vid[0].json())
        else:
            res.append(True)

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
        data['user']['isManager'] = any(request.user.groups.filter(name='manager')) or request.user.is_staff
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


@login_required()
def userList(request):
    res = Result()

    for user in User.objects.filter(is_active=True).order_by('first_name'):
        res.append(userToJson(user))

    return JsonResponse(res.asDict())


@ensure_csrf_cookie
def csrf(request):
    res = Result()
    try:
        res.append(request.COOKIES['csrftoken'])
    except KeyError:
        pass
    return JsonResponse(res.asDict())


def siteConfig(request):
    res = Result()
    res.append(getSiteConfig())

    return JsonResponse(res.asDict())


def clientError(request):
    data = json.loads(request.body)['body']
    message = str(data)
    try:
        message = data['error'].replace('\\n', '\n')
    except:
        pass
    
    mail_admins('Client Error', message)

    return JsonResponse({})


@require_http_methods(['GET'])
def releaseNotes(request):
    res = Result()
    lastid = request.GET.get('lastid', 0)
    today = datetime.datetime.today()
    relevent = today - datetime.timedelta(days=30)

    notes = ReleaseNotes.objects.filter(date__gte=relevent, pk__gt=lastid).order_by('-id')

    for note in notes:
        res.append(note.json())

    return JsonResponse(res.asDict())
