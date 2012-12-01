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


import logging
import re
import json
import time
import subprocess
import shutil
from threading import Thread

from django.conf import settings

from path import path as Path

TIMEOUT = 1
ROOT = Path(settings.MEDIA_ROOT.replace('\\', '/'))
logger = logging.getLogger('dev.frog')


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
                    logger.info('processing')
                    item.video = 'frog/i/processing.mp4'
                    item.save()
                    ## -- Set the status of the queue item
                    item.queue.setStatus(item.queue.Processing)
                    item.queue.setMessage('Processing video...')
                    
                    infile = "%s%s" % (ROOT, item.source.name)
                    cmd = '%s -i "%s"' % (settings.FFMPEG, infile)
                    sourcepath = ROOT / item.source.name

                    ## -- Get the video information
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    infoString = proc.stdout.readlines()
                    videodata = parseInfo(infoString)
                    isH264 = videodata['video'][0]['codec'].find('h264') != -1
                    m, s = divmod(settings.SCRUB_DURATION, 60)
                    h, m = divmod(m, 60)
                    scrubstr = "%02d:%02d:%02d" % (h, m, s)
                    scrub = videodata['duration'] <= scrubstr

                    outfile = sourcepath.parent / ("_%s.mp4" % item.hash)

                    ## -- Further processing is needed if not h264 or needs to be scrubbable
                    if not isH264 or scrub:
                        item.queue.setMessage('Converting to MP4...')
                        
                        cmds = '{exe} -i "{infile}" {args} "{outfile}"'.format(
                            exe=settings.FFMPEG,
                            infile=infile,
                            args=settings.SCRUB_FFMPEG_ARGS if scrub else settings.FFMPEG_ARGS,
                            outfile=outfile,
                        )
                        proc = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        proc.communicate()

                    ## -- Set the video to the result
                    logger.info('Done')
                    item.video = outfile.replace('\\', '/').replace(ROOT, '')
                    item.queue.setStatus(item.queue.Completed)
                    item.save()
                except Exception, e:
                    logger.error(str(e))

                time.sleep(TIMEOUT)


def parseInfo(strings):
    data = {}
    stream_video = re.compile("""Stream #\d:(?P<index>\d+).*: (?P<type>\w+): (?P<codec>.*), (?P<pixel_format>\w+), (?P<width>\d+)x(?P<height>\d+)""")
    stream_audio = re.compile("""Stream #\d:(?P<index>\d+).*: (?P<type>\w+): (?P<codec>.*), (?P<hertz>\d+) Hz, .*, .*, (?P<bitrate>\d+) kb/s$""")
    input_ = re.compile(""" '([a-zA-Z0-9\. ]+)':$""")
    duration = re.compile("""Duration: (?P<duration>\d+:\d+:\d+.\d+), start: (?P<start>\d+.\d+), bitrate: (?P<bitrate>\d+) kb/s$""")

    for n in strings:
        n = n.strip()
        #if n.startswith('Input'):
            #data['name'] = input_.findall(n)[0]
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