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

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

from frog.models import Gallery, Image, Video, Tag, Piece, DefaultPrefs

from frog.common import Result, JsonResponse, getObjectsFromGuids, userToJson
from frog.uploader import upload
from frog.signals import frog_auth_check

from frog.sendFile import send_zipfile


LOGGER = logging.getLogger('frog')
INDEX_HTML = getattr(settings, 'FROG_INDEX', 'frog/index.html')


@csrf_exempt
def index(request):
    if request.method == 'GET':
        frog_auth_check.send(sender=None, request=request)

        if not request.user.is_anonymous():
            return HttpResponseRedirect('/frog/gallery/1')
        return render(request, INDEX_HTML)
    else:
        return upload(request)

def login_(request):
    res = Result()

    res.isSuccess = True
    email = request.POST.get('email', 'noauthor@domain.com').lower()
    username = email.split('@')[0]
    password = request.POST.get('password')
    
    if password is None:
        ## -- SimpleAuth
        first_name = request.POST.get('first_name', 'no').lower()
        last_name = request.POST.get('last_name', 'author').lower()
        user = authenticate(username=username)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
    else:
        ## -- LDAP
        user = authenticate(username=username, password=password)
        
        if user is None:
            return render(request, 'frog/index.html', {'message': 'Invalid Credentials'})

        if not user.is_active:
            return render(request, 'frog/index.html', {'message': 'User account not active'})

    ## -- Create an artist tag for them
    Tag.objects.get_or_create(name=user.first_name + ' ' + user.last_name, defaults={'artist': True})

    ## -- Log them in
    login(request, user)

    return HttpResponseRedirect('/frog/gallery/1')

def logout_(request):
    logout(request)

    return HttpResponseRedirect('/frog')

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

        res.isSuccess = True
        res.append(userToJson(author))
        res.value['tag'] = Tag.objects.get(name=artist.lower()).id
    else:
        res.isError = True
        res.message = "No artist provided"

    return JsonResponse(res)

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

    return JsonResponse(res.values)

@login_required
def helpMe(request):
    msg = request.POST.get('message')
    toAddr = [m[1] for m in settings.MANAGERS]
    send_mail('Frog Help', msg, request.user.email, toAddr)

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

        res.isSuccess = True
    else:
        res.isError = True
        res.message = "No path provided"

    return JsonResponse(res)

def getUser(request):
    res = Result()
    if request.user.is_anonymous():
        res.isError = True
        res.append(DefaultPrefs)
    else:
        galleryid = request.GET.get('gallery')
        if galleryid is not None:
            gallery = Gallery.objects.filter(pk=galleryid, owner=request.user)
            if gallery:
                res.append(gallery[0].json())
        res.isSuccess = True

    return JsonResponse(res)
