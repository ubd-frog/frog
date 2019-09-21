import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use a very simple auth system
AUTHENTICATION_BACKENDS = ('frog.auth.SimpleAuthBackend',)

# Where are we storing our asset files?
MEDIA_ROOT = '/mnt/static/'
MEDIA_URL = 'static/'

# ffmpeg executable locations
FROG_FFMPEG = '/usr/bin/ffmpeg'
FROG_FFPROBE = '/usr/bin/ffprobe'

# Used in email links
FROG_SITE_URL = 'http://127.0.0.1/'
