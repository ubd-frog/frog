

from settings import MEDIA_URL, MEDIA_ROOT

def media(request):
    obj = {
        'MEDIA_URL': MEDIA_URL,
        'MEDIA_ROOT': MEDIA_ROOT,
        'isAjax': request.is_ajax(),
    }

    return obj