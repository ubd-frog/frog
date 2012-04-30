from pprint import pprint
import shutil
import hashlib
try:
    import ujson as json
except ImportError:
    import json

from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from models import Piece, Image, Video
from common import JsonResponse, Result, uniqueID, getHashForFile

from dev.settings import MEDIA_ROOT

from path import path as Path


class Uploader(object):
    def __init__(self):
        pass

    @csrf_exempt
    def post(self, request):
        res = Result()
        for filename, f in request.FILES.iteritems():
            try:
                filename = f.name
                paths = json.loads(request.POST.get('paths', '{}').replace("'", "\""))
                foreignPath = paths.get(filename, "%s/%s"% (uniqueID(), filename))
                galleries = request.POST.get('galleries', '').split(',');
                print 'galleries:', galleries
                
                uniqueName = Piece.getUniqueID(foreignPath, request.user)
                
                if f.content_type.startswith('image'):
                    model = Image
                else:
                    model = Video

                if request.user.is_anonymous():
                    user = User.objects.get(username=request.POST.get('user', 'noauthor'))
                else:
                    user = request.user

                obj, created = model.objects.get_or_create(unique_id=uniqueName, defaults={'author': user})
                guid = obj.getGuid()
                hashVal = getHashForFile(f);

                if hashVal == obj.hash:
                    res.isSuccess = True
                    return JsonResponse(res)

                objPath = Path(MEDIA_ROOT) / guid.guid[-2:] / guid.guid / filename
                hashPath = objPath.parent / hashVal + objPath.ext
                
                if not objPath.parent.exists():
                    objPath.parent.makedirs()

                self.handle_uploaded_file(hashPath, f)

                obj.hash = hashVal
                obj.foreign_path = foreignPath
                obj.title = objPath.namebase
                obj.export(hashVal, hashPath, galleries=galleries)

                res.append(obj.json())
            except Exception, e:
                res.isError = True
                res.message = str(e)
                print e
                return JsonResponse(res)

        res.isSuccess = True

        return JsonResponse(res)

    def handle_uploaded_file(self, dest, f):
        destination = open(dest, 'wb+')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()

        return True


uploader = Uploader()