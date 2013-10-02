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


import logging
import re
import time
import subprocess
from threading import Thread

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from path import path as Path

TIMEOUT = 1
ROOT = Path(settings.MEDIA_ROOT.replace('\\', '/'))
logger = logging.getLogger('frog')

try:
    FROG_FFMPEG = getattr(settings, 'FROG_FFMPEG')
except AttributeError:
    raise ImproperlyConfigured, 'FROG_FFMPEG is required'

FROG_SCRUB_DURATION = getattr(settings, 'FROG_SCRUB_DURATION', 60)
FROG_FFMPEG_ARGS = getattr(settings, 'FROG_FFMPEG_ARGS', '-vcodec libx264 -b:v 2500k -acodec libvo_aacenc -b:a 56k -ac 2 -y')
FROG_SCRUB_FFMPEG_ARGS = getattr(settings, 'FROG_SCRUB_FFMPEG_ARGS', '-vcodec libx264 -b:v 2500k -x264opts keyint=1:min-keyint=8 -acodec libvo_aacenc -b:a 56k -ac 2 -y')


class VideoThread(Thread):
    def __init__(self, queue, *args, **kwargs):
        super(VideoThread, self).__init__(*args, **kwargs)
        self.queue = queue
        self.daemon = True

    def run(self):
        while True:
            if self.queue.qsize():
                try:
                    isH264 = False
                    ## -- Get the video object to work on
                    item = self.queue.get()
                    ## -- Set the video to processing
                    logger.info('Processing video: %s' % item.guid)
                    item.video = 'frog/i/processing.mp4'
                    item.save()
                    ## -- Set the status of the queue item
                    item.queue.setStatus(item.queue.PROCESSING)
                    item.queue.setMessage('Processing video...')
                    
                    infile = "%s%s" % (ROOT, item.source.name)
                    cmd = '%s -i "%s"' % (FROG_FFMPEG, infile)
                    sourcepath = ROOT / item.source.name

                    ## -- Get the video information
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                    infoString = proc.stdout.readlines()
                    videodata = parseInfo(infoString)
                    isH264 = videodata['video'][0]['codec'].lower().find('h264') != -1 and sourcepath.ext == '.mp4'
                    m, s = divmod(FROG_SCRUB_DURATION, 60)
                    h, m = divmod(m, 60)
                    scrubstr = "%02d:%02d:%02d" % (h, m, s)
                    scrub = videodata['duration'] <= scrubstr

                    outfile = sourcepath.parent / ("_%s.mp4" % item.hash)

                    ## -- Further processing is needed if not h264 or needs to be scrubbable
                    if not isH264 or scrub:
                        item.queue.setMessage('Converting to MP4...')
                        
                        cmd = '{exe} -i "{infile}" {args} "{outfile}"'.format(
                            exe=FROG_FFMPEG,
                            infile=infile,
                            args=FROG_SCRUB_FFMPEG_ARGS if scrub else FROG_FFMPEG_ARGS,
                            outfile=outfile,
                        )
                        try:
                            subprocess.call(cmd, shell=True)
                        except subprocess.CalledProcessError:
                            logger.error('Failed to convert video: %s' % item.guid)
                            item.queue.setStatus(item.queue.ERROR)
                            continue
                        
                        item.video = outfile.replace('\\', '/').replace(ROOT, '')
                    else:
                        ## -- No further processing
                        item.video = item.source.name

                    ## -- Set the video to the result
                    logger.info('Finished processing video: %s' % item.guid)
                    item.queue.setStatus(item.queue.COMPLETED)
                    item.save()
                except Exception, e:
                    logger.error(str(e))

                time.sleep(TIMEOUT)


def parseInfo(strings):
    data = {}
    stream_video = re.compile("""Stream #\d[:.](?P<index>\d+).*: (?P<type>\w+): (?P<codec>.*), (?P<pixel_format>\w+), (?P<width>\d+)x(?P<height>\d+)""")
    stream_audio = re.compile("""Stream #\d[:.](?P<index>\d+).*: (?P<type>\w+): (?P<codec>.*), (?P<hertz>\d+) Hz, .*, .*, (?P<bitrate>\d+) kb/s$""")
    duration = re.compile("""Duration: (?P<duration>\d+:\d+:\d+.\d+), start: (?P<start>\d+.\d+), bitrate: (?P<bitrate>\d+) kb/s$""")

    for n in strings:
        n = n.strip()
        if n.startswith('Duration'):
            r = duration.search(n)
            data.update(r.groupdict())
        elif n.startswith('Stream'):
            if n.find('Video') != -1:
                data.setdefault('video', [])
                r = stream_video.search(n)
                data['video'].append(r.groupdict())
            elif n.find('Audio') != -1:
                data.setdefault('audio', [])
                r = stream_audio.search(n)
                data['audio'].append(r.groupdict())

    return data