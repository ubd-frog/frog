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
import subprocess
import logging.config
from collections import namedtuple
from threading import Thread, Event

import django
django.setup()
from django.conf import settings
from django.core.mail import send_mail, mail_admins
from django.template.loader import render_to_string
from django.core.exceptions import ImproperlyConfigured

from frog import getRoot
from frog.models import VideoQueue, FROG_SITE_URL

try:
    FROG_FFMPEG = getattr(settings, 'FROG_FFMPEG')
    FROG_FFPROBE = getattr(settings, 'FROG_FFPROBE')
except AttributeError:
    raise ImproperlyConfigured('FROG_FFMPEG and FROG_FFPROBE are required')

FROG_SCRUB_DURATION = getattr(settings, 'FROG_SCRUB_DURATION', 60)
FROG_FFMPEG_ARGS = getattr(settings, 'FROG_FFMPEG_ARGS', '-vcodec libx264 -b:v {}k -acodec libfdk_aac -b:a 56k -ac 2 -y')
FROG_SCRUB_FFMPEG_ARGS = getattr(settings, 'FROG_SCRUB_FFMPEG_ARGS', '-vcodec libx264 -b:v {}k -x264opts keyint=1:min-keyint=8 -acodec libfdk_aac -b:a 56k -ac 2 -y')

TIMEOUT = 1
ROOT = getRoot()
LOGGER = logging.getLogger('frog.video')
QUALITY = {
    'low': 1250,
    'medium': 2500,
    'high': 4000,
}


class VideoThread(Thread):

    def __init__(self, quality='medium', alwaysconvert=False, emailuser=True, *args, **kwargs):
        super(VideoThread, self).__init__(*args, **kwargs)
        self.daemon = True
        self.stop_event = Event()

        self._quality = quality
        self._alwaysconvert = alwaysconvert
        self._emailuser = emailuser

    def stop(self):
        self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            item = VideoQueue.objects.filter(status=VideoQueue.QUEUED).first()
            if not item:
                self.stop_event.wait(TIMEOUT)
                continue

            LOGGER.info('Working on %s', item.video.guid)

            try:
                LOGGER.info('Starting the process...')
                video = item.video

                # -- Set the video to processing
                LOGGER.info('Processing video: %s' % video.guid)
                item.status = VideoQueue.PROCESSING
                item.message = 'Processing video...'
                video.video = 'frog/i/processing.mp4'
                item.save()

                sourcepath = ROOT / video.source.name

                # -- Get the video information
                videodata = video.info()
                isH264 = 'h264' in videodata['streams'][0]['codec_name'].lower() and sourcepath.ext == '.mp4'
                scrub = float(videodata['streams'][0]['duration']) <= FROG_SCRUB_DURATION

                outfile = sourcepath.parent / '{}.mp4'.format(video.hash)

                # -- Further processing is needed if not h264 or needs to be scrubbable
                if not isH264 or scrub or self._alwaysconvert:
                    item.message = 'Converting to MP4...'
                    item.save()

                    ffmpegargs = FROG_SCRUB_FFMPEG_ARGS if scrub else FROG_FFMPEG_ARGS
                    cmd = '{exe} -i "{infile}" {args} "{outfile}"'.format(
                        exe=FROG_FFMPEG,
                        infile=sourcepath,
                        args=ffmpegargs.format(QUALITY[self._quality]),
                        outfile=outfile,
                    )
                    try:
                        subprocess.call(cmd, shell=True)
                    except subprocess.CalledProcessError as err:
                        LOGGER.error('Failed to convert video: %s' % video.guid)
                        item.status = VideoQueue.ERROR
                        item.message = str(err)
                        item.save()
                        continue

                    video.video = outfile.replace('\\', '/').replace(ROOT, '')
                else:
                    # -- No further processing
                    video.video = video.source.name

                # -- Set the video to the result
                LOGGER.info('Finished processing video: %s' % video.guid)
                item.delete()
                video.save()

                if self._emailuser:
                    # -- Email User
                    emailUser(video)
            except Exception as err:
                LOGGER.error(str(err))
                emailUser(item.video, err)
                mail_admins('Video Processing Failure', err)
                item.status = VideoQueue.ERROR
                item.save()


def emailUser(video, error=None):
    """Emails the author of the video that it has finished processing"""
    html = render_to_string('frog/video_email.html', {
        'user': video.author,
        'error': error,
        'video': video,
        'SITE_URL': FROG_SITE_URL,
    })
    subject, from_email, to = 'Video Processing Finished{}'.format(error or ''), 'noreply@frogmediaserver.com', video.author.email
    text_content = 'This is an important message.'
    html_content = html

    send_mail(subject, text_content, from_email, [to], html_message=html_content)


if __name__ == '__main__':
    LOGGER.info('Starting Worker')
    try:
        thread = VideoThread()
        thread.start()
        thread.join()
    except Exception as err:
        LOGGER.error(err)

