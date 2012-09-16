import logging
import re
import json
import time
import subprocess
import shutil
from threading import Thread

from settings import MEDIA_ROOT, FFMPEG, FFMPEG_ARGS, SCRUB_DURATION, SCRUB_FFMPEG_ARGS

from path import path as Path

TIMEOUT = 1
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
                    
                    infile = "%s%s" % (MEDIA_ROOT, item.source.name)
                    cmd = '%s -i "%s"' % (FFMPEG, infile)
                    sourcepath = Path(MEDIA_ROOT) / item.source.name

                    ## -- Get the video information
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    infoString = proc.stdout.readlines()
                    videodata = parseInfo(infoString)
                    isH264 = videodata['video'][0]['codec'].find('h264') != -1
                    m, s = divmod(SCRUB_DURATION, 60)
                    h, m = divmod(m, 60)
                    scrubstr = "%02d:%02d:%02d" % (h, m, s)
                    scrub = videodata['duration'] <= scrubstr

                    outfile = sourcepath.parent / ("_%s.mp4" % item.hash)

                    ## -- Further processing is needed if not h264 or needs to be scrubbable
                    if not isH264 or scrub:
                        item.queue.setMessage('Converting to MP4...')
                        
                        cmds = '{exe} -i "{infile}" {args} "{outfile}"'.format(
                            exe=FFMPEG,
                            infile=infile,
                            args=SCRUB_FFMPEG_ARGS if scrub else FFMPEG_ARGS,
                            outfile=outfile,
                        )
                        proc = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        proc.communicate()

                    ## -- Set the video to the result
                    logger.info('Done')
                    item.video = outfile.replace('\\', '/').replace(MEDIA_ROOT, '')
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