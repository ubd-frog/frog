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


from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from common import PluginContext, getRoot

try:
    FROG_SITE_URL = getattr(settings, 'FROG_SITE_URL')
except AttributeError:
    raise ImproperlyConfigured, 'FROG_SITE_URL is required'


BUILD = 1003

def media(request):
    obj = {
        'MEDIA_URL': settings.MEDIA_URL,
        'MEDIA_ROOT': getRoot(),
        'isAjax': request.is_ajax(),
        'plugins': PluginContext,
        'build': BUILD,
        'SITE_URL': FROG_SITE_URL,
    }
    print obj
    return obj