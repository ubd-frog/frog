

from dev.settings import MEDIA_URL, MEDIA_ROOT

def media(request):
    obj = {
        'MEDIA_URL': MEDIA_URL,
        'MEDIA_ROOT': MEDIA_ROOT,
    }
    print obj

    return obj