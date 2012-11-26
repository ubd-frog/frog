"""
Copyright (c) 2012 Brett Dixon

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
Software, and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os
import time
import logging
try:
    import ujson as json
except ImportError:
    import json

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.contrib.comments.models import Comment
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.conf import settings

try:
    from haystack.query import SearchQuerySet
    HAYSTACK = True
except ImportError:
    HAYSTACK = False

from models import Gallery, Image, Video, Tag, Piece, UserPref, DefaultPrefs

from common import MainView, Result, JsonResponse, getObjectsFromGuids, commentToJson, userToJson
from uploader import uploader
from signals import frog_auth_check

from sendFile import send_file, send_zipfile


logger = logging.getLogger('dev.frog')
LoginRequired = method_decorator(login_required)


class GalleryView(MainView):
    def __init__(self):
        super(GalleryView, self).__init__(Gallery)

    def get(self, request, obj_id=None):
        if obj_id:
            obj = self._getObject(obj_id)
            if obj.private and request.user.is_anonymous():
                return HttpResponseRedirect('/frog')

            return super(GalleryView, self).get(request, obj_id)
        else:
            res = Result()
            res.isSuccess = True
            if request.user.is_anonymous():
                objects = Gallery.objects.filter(private=False)
            else:
                objects = Gallery.objects.filter(Q(private=False) | Q(owner=request.user))

            for n in objects:
                res.append(n.json())

            return JsonResponse(res)

    @LoginRequired
    def post(self, request):
        """ Create a Gallery """
        title = request.POST.get('title', 'New Gallery' + str(Gallery.objects.all().values_list('id', flat=True)[0] + 1))
        description = request.POST.get('description', '')
        private = json.loads(request.POST.get('private', 'false'))
        g, created = Gallery.objects.get_or_create(title=title)
        g.description = description
        g.private = private
        g.owner = request.user
        g.save()

        res = Result()
        res.isSuccess = True
        res.append(g.json())
        res.message = 'Gallery created' if created else ''

        return JsonResponse(res)

    @LoginRequired
    def put(self, request, obj_id=None):
        """ Adds Image and Video objects to Gallery based on GUIDs """
        guids = filter(None, request.PUT.get('guids', '').split(','))
        private = request.PUT.get('private')
        move = request.PUT.get('move')
        object_ = self._getObject(obj_id)
        
        if guids:
            objects = getObjectsFromGuids(guids)

            images = filter(lambda x: isinstance(x, Image), objects)
            videos = filter(lambda x: isinstance(x, Video), objects)

            object_.images.add(*images)
            object_.videos.add(*videos)
        
        if private is not None:
            object_.private = json.loads(private)
            object_.save()

        res = Result()
        res.append(object_.json())
        res.isSuccess = True

        return JsonResponse(res)

    @LoginRequired
    def delete(self, request, obj_id=None):
        """ Removes Image/Video objects from Gallery """
        guids = request.DELETE.get('guids', '').split(',')
        objects = getObjectsFromGuids(guids)
        object_ = self._getObject(obj_id)

        for o in objects:
            if isinstance(o, Image):
                object_.images.remove(o)
            elif isinstance(o, Video):
                object_.videos.remove(o)

        res = Result()
        res.isSuccess = True

        return JsonResponse(res)

    def filter(self, request, obj_id):
        """
        Filters Gallery for the requested Image/Video objects.  Returns a Result object with 
        serialized objects
        """
        obj = self._getObject(obj_id)

        if request.user.is_anonymous() and obj.private:
            res = Result()
            res.isError = True
            res.message = 'This gallery is private'

            return JsonResponse(res)

        
        tags = json.loads(request.GET.get('filters', '[[]]'))
        rng = request.GET.get('rng', None)
        more = request.GET.get('more', False)
        models = request.GET.get('models', 'image,video')
        if models == '':
            models = 'image,video'

        tags = filter(None, tags)

        models = [ContentType.objects.get(app_label='frog', model=x) for x in models.split(',')]

        return self._filter(request, obj, tags=tags, rng=rng, models=models, more=more)

    def _filter(self, request, object_, tags=None, models=(Image, Video), rng=None, more=False):
        """
        Filters Piece objects from self based on filters, search, and range

        tags -- list, List of tag IDs to filter
        models -- list, List of model classes to filter on
        rng -- string, Range of objects to return. i.e. 0:100
        more -- bool, Returns more of the same filtered set of images based on session range

        return list, Objects filtered
        """
        
        NOW = time.clock()

        res = Result()
        
        idDict = {}
        objDict = {}
        lastIDs = {}
        data = {}

        logger.debug('init: %f' % (time.clock() - NOW))

        #Prefs = json.loads(UserPref.objects.get(user=request.user).data)
        gRange = 300#Prefs['batchSize']
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
            logger.debug(m.model + '_initial_query: %f' % (time.clock() - NOW))

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
                                logger.debug('search From LIKE')
                                o |= Q(title__icontains=item)
                    if HAYSTACK and searchQuery != "":
                        ## -- once all tags have been filtered, filter by search
                        searchIDs = self._search(searchQuery)
                        if searchIDs:
                            if not o:
                                o = Q()
                            logger.debug('searchFrom haystack:' + str(searchIDs))
                            o |= Q(id__in=searchIDs)

                    if o:
                        ## -- apply the filters
                        idDict[m.model] = idDict[m.model].filter(o)
                    else:
                        idDict[m.model] = idDict[m.model].none()

                logger.debug(m.model + '_added_buckets(%i): %f' % (len(tags), time.clock() - NOW))
            
            ## -- Get all ids of filtered objects, this will be a very fast query
            idDict[m.model] = list(idDict[m.model].values_list('id', flat=True))
            logger.debug(m.model + '_queried_ids: %f' % (time.clock() - NOW))

            res.message = str(s) + ':' + str(e)
            
            ## -- perform the main query to retrieve the objects we want
            objDict[m.model] = m.model_class().objects.filter(id__in=idDict[m.model]).select_related('author').prefetch_related('tags')
            if not rng:
                objDict[m.model] = objDict[m.model][:gRange]
            objDict[m.model] = list(objDict[m.model])
            logger.debug(m.model + '_queried_obj: %f' % (time.clock() - NOW))
        
        
        ## -- combine and sort all objects by date
        objects = self._sortObjects(**objDict) if len(models) > 1 else objDict.values()[0]
        objects = objects[s:e]
        logger.debug('sorted: %f' % (time.clock() - NOW))

        ## -- serialize objects
        for i in objects:
            for m in models:
                if isinstance(i, m.model_class()):
                    ## -- set the last ID per model for future lookups
                    lastIDs['last_%s_id' % m.model] = i.id
                    data['last_%s_id' % m.model] = i.id
            res.append(i.json())
        logger.debug('serialized: %f' % (time.clock() - NOW))

        request.session['frog_range'] = ':'.join((str(s),str(e)))

        logger.debug('total: %f' % (time.clock() - NOW))
        request.session['last_image_id'] = lastIDs.get('last_image_id', 0)
        request.session['last_video_id'] = lastIDs.get('last_video_id', 0)
        
        data['count'] = len(objects)
        data['queries'] = connection.queries

        res.value = data

        res.isSuccess = True

        return JsonResponse(res)

    def _sortObjects(self, **args):
        """ Sort and combine objects """
        o = []
        
        for m in args.values():
            for l in iter(m):
                o.append(l)
        o = list(set(o))
        o.sort(self._sortByCreated)

        return o

    def _sortByCreated(self, a, b):
        """ Sort function for object by created date """
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

    def _search(self, query):
        """ Performs a search query and returns the object ids """
        query = query.strip()
        logger.debug(query)
        return [o.object.id for o in SearchQuerySet().auto_query(query).load_all()]


class TagView(MainView):
    def __init__(self):
        super(TagView, self).__init__(Tag)

    def get(self, request, obj_id=None):
        if obj_id:
            return super(TagView, self).get(request, obj_id)
        else:
            res = Result()
            res.isSuccess = True
            for n in Tag.objects.all():
                res.append(n.json())

            return JsonResponse(res)

    @LoginRequired
    def post(self, request, obj_id=None):
        res = Result()
        if not obj_id:
            name = request.POST.get('name', None)

            if not name:
                res.isError = True
                res.message = "No name given"

                return JsonResponse(res)
            
            tag, created = Tag.objects.get_or_create(name=name)

            res.isSuccess = True
            if created:
                res.message = "Created"

            res.append(tag.json())

            return JsonResponse(res)

    @LoginRequired
    def put(self, request, obj_id=None):
        tagList = filter(None, request.PUT.get('tags', '').split(','))
        guids = request.PUT.get('guids', '').split(',')
        res = Result()
        res.isSuccess = True

        self._manageTags(tagList, guids)

        return JsonResponse(res)

    @LoginRequired
    def delete(self, request, obj_id=None):
        tagList = filter(None, self.DELETE.get('tags', '').split(','))
        guids = self.DELETE.get('guids', '').split(',')
        res = Result()
        res.isSuccess = True

        self._manageTags(tagList, guids, add=False)

        return JsonResponse(res)

    def search(self, request):
        """
        Search for Tag objects and returns a Result object with a list of searialize Tag
        objects.

        -- search: bool, Append a "Search for" tag
        -- zero: bool, Exclude Tags with no items
        -- artist: bool, Exclude artist tags
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

    @LoginRequired
    def manage(self, request):
        if request.method == 'GET':
            guids = request.GET.get('guids', '').split(',')
            guids = filter(None, guids)

            objects = getObjectsFromGuids(guids)
            ids = [o.id for o in objects]

            tags = list(set(Tag.objects.filter(image__id__in=ids).exclude(artist=True)))

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

            add = filter(None, add)
            rem = filter(None, rem)
            addList = []

            for t in add:
                try:
                    addList.append(int(t))
                except ValueError:
                    tag, created = Tag.objects.get_or_create(name=t)
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

    def _manageTags(self, tagList, guids, add=True):
        """ Adds or Removed Guids from Tags """
        objects = getObjectsFromGuids(guids)
        tags = []
        for tag in tagList:
            try:
                t = Tag.objects.get(pk=int(tag))
            except ValueError:
                t, created = Tag.objects.get_or_create(name=tag)
            tags.append(t)

        if add:
            return self._addTags(tags, objects)
        else:
            return self._removeTags(tags, objects)

    def _addTags(self, tags, objects):
        """ Adds tags to objects """
        for t in tags:
            for o in objects:
                o.tags.add(t)

        return True

    def _removeTags(self, tags, objects):
        """ Removes tags from objects """
        for t in tags:
            for o in objects:
                o.tags.remove(t)

        return True


class ImageView(MainView):
    def __init__(self, model=None):
        model = model or Image
        super(ImageView, self).__init__(model)

    @LoginRequired
    def post(self, request, obj_id):
        object_ = self._getObject(obj_id)
        tags = request.POST.get('tags', '').split(',')
        res = Result()
        for tag in tags:
            try:
                t = Tag.objects.get(pk=int(tag))
            except ValueError:
                t, created = Tag.objects.get_or_create(name=tag)
                if created:
                    res.append(t.json())
            object_.tags.add(t)

        res.isSuccess = True

        return JsonResponse(res)

    @LoginRequired
    def delete(self, request, obj_id):
        object_ = self._getObject(obj_id)
        object_.deleted = True
        object_.save()
        res = Result()
        res.isSuccess = True
        res.value = object_.json()
        return JsonResponse(res)


class VideoView(ImageView):
    def __init__(self):
        super(VideoView, self).__init__(Video)


class UserPrefView(MainView):
    def __init__(self):
        super(UserPrefView, self).__init__(UserPref)

    def get(self, request):
        res = Result()
        obj, created = self.model.objects.get_or_create(user=request.user)
        if created:
            obj.data = json.dumps(DefaultPrefs.copy())
            obj.save()
        res.append(obj.json())
        res.isSuccess = True

        return JsonResponse(res)

    @LoginRequired
    def post(self, request):
        key = request.POST.get('key', None)
        val = request.POST.get('val', None)
        res = Result()
        if key and val:
            obj, created = self.model.objects.get_or_create(user=request.user)
            if created:
                obj.data = json.dumps(DefaultPrefs.copy())
                obj.save()
            val = json.loads(val)
            obj.setKey(key, val)
            obj.save()
            res.append(obj.json())
            res.isSuccess = True
        else:
            res.isError = True
            res.message = 'No key and value provided'

        return JsonResponse(res)


class CommentView(MainView):
    def __init__(self):
        super(CommentView, self).__init__(Comment)

    @csrf_exempt
    def view(self, request, obj_id=None):

        if request.method == 'GET':
            return self.get(request, obj_id)
        elif request.method == 'POST':
            return self.post(request, obj_id)
        elif request.method == 'PUT':
            return self.put(request, obj_id)
        elif request.method == 'DELETE':
            return self.delete(request, obj_id)

    def get(self, request, obj_id=None):
        res = Result()
        if obj_id:
            c = Comment.objects.get(pk=obj_id)
            res.append(commentToJson(c))
            res.isSuccess = True

            return JsonResponse(res)

        guid = request.GET.get('guid', None)
        id = request.GET.get('id', 0)
        if guid:
            if request.GET.get('json', False):
                for c in Comment.objects.all():
                    res.append(commentToJson(c))

                res.isSuccess = True

                return JsonResponse(res)
            else:
                obj = getObjectsFromGuids([guid])[0]
                if obj.AssetType == 1:
                    model = 'image'
                else:
                    model = 'video'
                contentType = ContentType.objects.get(app_label="frog", model=model)
                comments = Comment.objects.filter(object_pk=obj.id, content_type=contentType)
                return render(request, 'frog/comment_list.html', {'comments': comments, 'guid': guid, 'id': id})

    @LoginRequired
    def post(self, request, obj_id=None):
        guid = request.POST.get('guid', None)
        res = Result()
        if obj_id:
            c = Comment.objects.get(pk=obj_id)
            newComment = request.POST.get('comment', None)
            if newComment:
                c.comment = newComment
                c.save()

                res.append(commentToJson(c))
                res.isSuccess = True
            else:
                res.isError = True
                res.message = "No comment provided"

            return JsonResponse(res)

        if guid:
            obj = getObjectsFromGuids([guid,])[0]
            c = Comment()
            c.comment = request.POST.get('comment', 'No comment')
            c.user = request.user
            c.user_name = request.user.get_full_name()
            c.user_email = request.user.email
            c.content_object = obj
            c.site_id = 1
            c.save()
            obj.comment_count = obj.comment_count + 1
            obj.save()

            self.email(c, obj)

            res.append({'id': c.id, 'comment': c.comment})
            res.isSuccess = True
        else:
            res.isError = True
            res.message = "No guid provided"

        return JsonResponse(res)

    def email(self, comment, obj):
        html = render_to_string('frog/comment_email.html', {
            'comment': comment,
            'object': obj,
        })
        subject, from_email, to = 'Comment from %s' % comment.user_name, '%s (%s)' % (comment.user_name, comment.user_email), obj.author.email
        text_content = 'This is an important message.'
        html_content = html
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


@login_required
def downloadView(request):
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

@csrf_exempt
def index(request):
    if request.method == 'GET':
        frog_auth_check.send(sender=None, request=request)

        if not request.user.is_anonymous():
            return HttpResponseRedirect('/frog/gallery/1')
        return render(request, 'frog/index.html', {'title': 'Frog Login'})
    else:
        return uploader.post(request)

def frogLogin(request):
    res = Result()

    res.isSuccess = True
    email = request.POST.get('email', 'noauthor@domain.com').lower()
    username = email.split('@')[0]
    first_name = request.POST.get('first_name', 'no').lower()
    last_name = request.POST.get('last_name', 'author').lower()

    user = authenticate(username=username)
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.save()

    Tag.objects.get_or_create(name=first_name + ' ' + last_name, defaults={'artist': True})

    if user.is_active:
        login(request, user)
        return HttpResponseRedirect('/frog/gallery/1')
    else:
        return render(request, 'frog/index.html', {'message': 'User account not active'})

def frogLogout(request):
    logout(request)

    return HttpResponseRedirect('/frog')

@login_required
def switchArtist(request):
    artist = request.POST.get('artist', None)
    guids = request.POST.get('guids', '').split(',')
    res = Result()
    if artist:
        first, last = artist.lower().split(' ')
        author = User.objects.get_or_create(first_name=first, last_name=last, defaults={
            'username': '%s%s' % (first[0], last),
            'email': '%s%s@%s' % (first[0], last, settings.DOMAIN),
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
    query = request.GET.get('q', False)
    if query:
        for n in User.objects.filter(first_name__icontains=query.lower()):
            res.append(userToJson(n))

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
        res.isSuccess = True

    return JsonResponse(res)


gallery = GalleryView()
tag = TagView()
image = ImageView()
video = VideoView()
pref = UserPrefView()
comment = CommentView()