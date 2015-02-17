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


from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from frog import models
from frog.common import JsonResponse, Result, getHashForFile

from path import path as Path

EXT = {
    'image': ['.jpg', '.png', '.gif', '.tif', '.tiff'],
    'video': ['.mp4', '.avi', '.wmv', '.mov']
}


class MediaTypeError(Exception):
    pass


@csrf_exempt
def upload(request):
    res = Result()
    f = request.FILES.get('file')

    if f:
        filename = f.name

        path = request.POST.get('path', None)
        if path:
            foreignPath = path.replace("'", "\"")
        else:
            foreignPath = filename

        galleries = request.POST.get('galleries', '1').split(',')
        tags = filter(None, request.POST.get('tags', '').split(','))

        try:
            username = request.POST.get('user', False)
            if username:
                user = User.objects.get(username=username)
            else:
                if request.user.is_anonymous():
                    username = 'noauthor'
                    user = User.objects.get(username=username)
                else:
                    user = request.user
            
            uniqueName = request.POST.get('uid', models.Piece.getUniqueID(foreignPath, user))
            
            if f.content_type.startswith('image'):
                if Path(filename).ext.lower() not in EXT['image']:
                    raise MediaTypeError
                model = models.Image
            else:
                if Path(filename).ext not in EXT['video']:
                    raise MediaTypeError
                model = models.Video

            obj, created = model.objects.get_or_create(unique_id=uniqueName, defaults={'author': user})
            guid = obj.getGuid()
            hashVal = getHashForFile(f)

            if hashVal == obj.hash:
                for gal in galleries:
                    g = models.Gallery.objects.get(pk=int(gal))
                    obj.gallery_set.add(g)
                res.isSuccess = True
                res.message = "Files were the same"

                return JsonResponse(res)

            objPath = models.ROOT
            if models.FROG_PATH:
                objPath = objPath / models.FROG_PATH
            objPath = objPath / guid.guid[-2:] / guid.guid / filename
            
            hashPath = objPath.parent / hashVal + objPath.ext
            
            if not objPath.parent.exists():
                objPath.parent.makedirs()

            handle_uploaded_file(hashPath, f)

            obj.hash = hashVal
            obj.foreign_path = foreignPath
            obj.title = objPath.namebase
            obj.export(hashVal, hashPath, tags=tags, galleries=galleries)

            res.append(obj.json())

            for key, f in request.FILES.items():
                if key != 'file':
                    dest = objPath.parent / f.name
                    handle_uploaded_file(dest, f)

            res.isSuccess = True
        except MediaTypeError:
            res.isError = True
            res.message = 'Filetype not supported'
            
            return JsonResponse(res)

    else:
        res.isError = True
        res.message = "No file found"

    return JsonResponse(res)

def handle_uploaded_file(dest, f):
    destination = open(dest, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()

    return True
