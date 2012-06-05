
import time
import subprocess
import shutil
from threading import Thread

from settings import MEDIA_ROOT, FFMPEG

from path import path as Path

TIMEOUT = 1

class VideoThread(Thread):
    def __init__(self, queue, *args, **kwargs):
        super(VideoThread, self).__init__(*args, **kwargs)

        self.queue = queue
        self.daemon = True

    def run(self):
        while True:
            if self.queue.qsize():
                isH264 = False
                item = self.queue.get()
                infile = "%s%s" % (MEDIA_ROOT, item.source.name)
                cmd = '%s -i "%s"' % (FFMPEG, infile)
                sourcePath = Path(MEDIA_ROOT) / item.source.name
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                infoString = proc.stdout.readlines()
                for n in infoString:
                    n = n.strip()
                    if n.startswith('Stream'):
                        if n.find('h264'):
                            videoPath = sourcePath.parent / '_%s.mp4' % item.hash
                            shutil.copy(sourcePath, videoPath)
                            item.video = videoPath.replace('\\', '/').replace(MEDIA_ROOT, '')
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

                time.sleep(TIMEOUT)