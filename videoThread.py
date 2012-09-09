
import re
import json
import time
import subprocess
import shutil
from threading import Thread

from settings import MEDIA_ROOT, FFMPEG, FFMPEG_ARGS, SCRUB_DURATION, SCRUB_FFMPEG_ARGS

from path import path as Path

TIMEOUT = 1


class JsonQueue(object):
    def __init__(self):
        self.f = Path(__file__).parent / 'video.json'
        self.data = None
        self._get()

    def _get(self):
        self.data = json.loads(self.f.text())

    def _set(self):
        self.f.write_text(json.dumps(self.data, indent=4))

    def pop(self):
        self._get()
        if self.data['queued']:
            obj = self.data['queued'].pop(0)
            self._set()

            return obj

        return None

    def append(self, obj):
        self._get()
        self.data['queued'].append(obj)
        self._set()

    def setBuilding(self, key, value):
        self._get()
        self.data['building'][key] = value
        self._set()

    def complete(self, obj):
        self._get()
        self.data['completed'].append(obj)
        self._set()

class VideoThread(Thread):
    def __init__(self, queue, *args, **kwargs):
        super(VideoThread, self).__init__(*args, **kwargs)
        self.json = JsonQueue()
        self.queue = queue
        self.daemon = True

    def run(self):
        while True:
            if self.queue.qsize():
                isH264 = False
                item = self.queue.get()
                self.json.pop()
                infile = "%s%s" % (MEDIA_ROOT, item.source.name)
                cmd = '%s -i "%s"' % (FFMPEG, infile)
                sourcepath = Path(MEDIA_ROOT) / item.source.name
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                infoString = proc.stdout.readlines()
                videodata = parseInfo(infoString)
                isH264 = videodata['video'][0]['codec'].find('h264') != -1
                m, s = divmod(SCRUB_DURATION, 60)
                h, m = divmod(m, 60)
                scrubstr = "%02d:%02d:%02d" % (h, m, s)
                scrub = videodata['duration'] <= scrubstr

                if not isH264 or scrub:
                    outfile = sourcepath.parent / ("_%s.mp4" % item.hash)
                    cmds = '{exe} -i "{infile}" {args} "{outfile}"'.format(
                        exe=FFMPEG,
                        infile=infile,
                        args=SCRUB_FFMPEG_ARGS if scrub else FFMPEG_ARGS,
                        outfile=outfile,
                    )
                    proc = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    proc.communicate()

                    item.video = outfile.replace('\\', '/').replace(MEDIA_ROOT, '')

                item.save()
                self.json.complete(item.json())

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