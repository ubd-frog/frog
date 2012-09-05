
import json
import time
import subprocess
import shutil
from threading import Thread

from settings import MEDIA_ROOT, FFMPEG

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
                for n in infoString:
                    n = n.strip()
                    if n.startswith('Stream'):
                        if n.find('h264'):
                            videopath = sourcepath.parent / '_%s.mp4' % item.hash
                            shutil.copy(sourcepath, videopath)
                            item.video = videopath.replace('\\', '/').replace(MEDIA_ROOT, '')
                            isH264 = True
                            break

                if not isH264:
                    outfile = "%s_%s.mp4" % (MEDIA_ROOT, item.hash)
                    cmds = '$exe -i "$infile" -vcodec libx264 -vpre hq -b 250k -bt 50k -acodec libfaac -ab 56k -ac 2 $outfile'.format(
                        exe=FFMPEG,
                        infile=infile,
                        outfile=outfile,
                    )
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    proc.communicate()

                    item.video = outfile.replace('\\', '/').replace(MEDIA_ROOT, '')

                item.save()
                self.json.complete(item.json())

                time.sleep(TIMEOUT)