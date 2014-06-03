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

from django.shortcuts import render
from django.contrib.comments.models import Comment
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string

from frog.common import Result, JsonResponse, commentToJson, getObjectsFromGuids, getPutData
from frog.models import FROG_SITE_URL


def index(request, obj_id):
    """Handles a request based on method and calls the appropriate function"""
    if request.method == 'GET':
        return get(request, obj_id)
    elif request.method == 'PUT':
        getPutData(request)
        return put(request)

def get(request, obj_id):
    """Returns a serialized object
    :param obj_id: ID of comment object
    :type obj_id: int
    :returns: json
    """
    res = Result()
    c = Comment.objects.get(pk=obj_id)
    res.append(commentToJson(c))
    res.isSuccess = True

    return JsonResponse(res)

@login_required
def post(request):
    """Returns a serialized object
    :param obj_id: ID of comment object
    :type obj_id: int
    :returns: json
    """
    guid = request.POST.get('guid', None)
    res = Result()   

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

        __email(c, obj)

        res.append({'id': c.id, 'comment': c.comment})
        res.isSuccess = True
    else:
        res.isError = True
        res.message = "No guid provided"

    return JsonResponse(res)

@login_required
def put(request, obj_id):
    """Updates the content of a comment
    :param obj_id: ID of comment object
    :type obj_id: int
    :returns: json
    """
    res = Result()
    c = Comment.objects.get(pk=obj_id)
    content = request.PUT.get('comment', None)
    if content:
        c.comment = content
        c.save()

        res.append(commentToJson(c))
        res.isSuccess = True
    else:
        res.isError = True
        res.message = "No comment provided"

    return JsonResponse(res)

@csrf_exempt
def commentList(request):
    """Returns a rendered list of comments
    :returns: html
    """
    if request.method == 'POST':
        return post(request)

    comments = []
    guid = request.GET.get('guid', None)
    id = request.GET.get('id', 0)
    if guid:
        obj = getObjectsFromGuids([guid])[0]
        if obj.AssetType == 1:
            model = 'image'
        else:
            model = 'video'
        contentType = ContentType.objects.get(app_label="frog", model=model)
        comments = Comment.objects.filter(object_pk=obj.id, content_type=contentType)
    
    return render(request, 'frog/comment_list.html', {'comments': comments, 'guid': guid, 'id': id})

def __email(comment, obj):
    """Returns a serialized object
    :param obj: Asset object that has the new comment
    :type obj_id: object
    """
    html = render_to_string('frog/comment_email.html', {
        'comment': comment,
        'object': obj,
        'SITE_URL': FROG_SITE_URL,
    })
    subject, from_email, to = 'Comment from %s' % comment.user_name, '%s (%s)' % (comment.user_name, comment.user_email), obj.author.email
    text_content = 'This is an important message.'
    html_content = html
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()