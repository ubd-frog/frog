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


from django.conf import settings

MEDIA_ROOT = settings.MEDIA_ROOT
MEDIA_URL = settings.MEDIA_URL
MANAGERS = settings.MANAGERS
## -- Absolute url
SITE_URL = 'http://127.0.0.1'
DOMAIN = 'gmail.com'
## -- Video settings
FFMPEG = 'C:/bin/ffmpeg.exe'
FFMPEG_ARGS = '-vcodec libx264 -b:v 2500k -acodec libvo_aacenc -b:a 56k -ac 2 -y'
SCRUB_FFMPEG_ARGS = '-vcodec libx264 -b:v 2500k -x264opts keyint=1:min-keyint=8 -acodec libvo_aacenc -b:a 56k -ac 2 -y'
SCRUB_DURATION = 60
## -- Image settings
IMAGE_SIZE_CAP = 5120
IMAGE_SMALL_SIZE = 600
THUMB_SIZE = 256