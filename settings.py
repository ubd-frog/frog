from django.conf import settings

MEDIA_ROOT = settings.MEDIA_ROOT
MEDIA_URL = settings.MEDIA_URL
MANAGERS = settings.MANAGERS
## -- Absolute url
SITE_URL = 'http://127.0.0.1:8080'
DOMAIN = 'gmail.com'
## -- Video settings
FFMPEG = 'C:/bin/ffmpeg.exe'
FFMPEG_ARGS = '-vcodec libx264 -b:v 2500k -y'
SCRUB_FFMPEG_ARGS = '-vcodec libx264 -b:v 2500k -x264opts keyint=1:min-keyint=8 -y'
SCRUB_DURATION = 60
## -- Image settings
IMAGE_SIZE_CAP = 5120
IMAGE_SMALL_SIZE = 600
THUMB_SIZE = 256