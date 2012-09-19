from path import path as Path

from settings import MEDIA_URL, MEDIA_ROOT
#from frog.common import PluginContext


def media(request):    
    obj = {
        'MEDIA_URL': MEDIA_URL,
        'MEDIA_ROOT': MEDIA_ROOT,
        'isAjax': request.is_ajax(),
        #'plugins': PluginContext,
    }

    return obj