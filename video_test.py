import re
import datetime
from pprint import pprint


s = """
ffmpeg version N-41195-g8a0efa9 Copyright (c) 2000-2012 the FFmpeg developers
  built on May 31 2012 20:04:59 with gcc 4.6.3
  configuration: --enable-gpl --enable-version3 --disable-w32threads --enable-runtime-cpudetect --enable-avisynth --enable-bzlib --enable-frei0r --enable-libass --enable-libcelt --
enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libfreetype --enable-libgsm --enable-libmp3lame --enable-libnut --enable-libopenjpeg --enable-librtmp --enable-libschro
edinger --enable-libspeex --enable-libtheora --enable-libutvideo --enable-libvo-aacenc --enable-libvo-amrwbenc --enable-libvorbis --enable-libvpx --enable-libx264 --enable-libxavs
--enable-libxvid --enable-zlib
  libavutil      51. 55.100 / 51. 55.100
  libavcodec     54. 23.100 / 54. 23.100
  libavformat    54.  6.101 / 54.  6.101
  libavdevice    54.  0.100 / 54.  0.100
  libavfilter     2. 77.100 /  2. 77.100
  libswscale      2.  1.100 /  2.  1.100
  libswresample   0. 15.100 /  0. 15.100
  libpostproc    52.  0.100 / 52.  0.100
Input #0, avi, from 'bunny.avi':
  Duration: 00:09:56.45, start: 0.000000, bitrate: 2957 kb/s
    Stream #0:0: Video: mpeg4 (Simple Profile) (FMP4 / 0x34504D46), yuv420p, 854x480 [SAR 1:1 DAR 427:240], 24 tbr, 24 tbn, 24 tbc
    Stream #0:1: Audio: ac3 ([0] [0][0] / 0x2000), 48000 Hz, 5.1(side), s16, 448 kb/s
At least one output file must be specified
"""

s2 = """
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'bunny.mp4':
  Metadata:
    major_brand     : mp42
    minor_version   : 0
    compatible_brands: mp42isomavc1
    creation_time   : 2011-03-29 05:41:33
    encoder         : HandBrake 0.9.5 2011010300
  Duration: 00:02:28.01, start: 0.000000, bitrate: 1054 kb/s
    Stream #0:0(und): Video: h264 (Constrained Baseline) (avc1 / 0x31637661), yuv420p, 640x360, 986 kb/s, 25 fps, 25 tbr, 90k tbn, 50 tbc
    Metadata:
      creation_time   : 2011-03-29 05:41:33
    Stream #0:1(und): Audio: aac (mp4a / 0x6134706D), 48000 Hz, stereo, s16, 64 kb/s
    Metadata:
      creation_time   : 2011-03-29 05:41:33
At least one output file must be specified
"""

s3 = """
Input #0, asf, from 'Wildlife.wmv':
  Metadata:
    SfOriginalFPS   : 299
    WMFSDKVersion   : 11.0.6001.7000
    WMFSDKNeeded    : 0.0.0.0000
    IsVBR           : 0
    title           : Wildlife in HD
    copyright       : ┬⌐ 2008 Microsoft Corporation
    comment         : Footage: Small World Productions, Inc; Tourism New Zealand | Producer: Gary F. Spradling | Music: Steve Ball
  Duration: 00:00:30.09, start: 0.000000, bitrate: 6977 kb/s
    Stream #0:0(eng): Audio: wmav2 (a[1][0][0] / 0x0161), 44100 Hz, stereo, s16, 192 kb/s
    Stream #0:1(eng): Video: vc1 (Advanced) (WVC1 / 0x31435657), yuv420p, 1280x720, 5942 kb/s, 29.97 tbr, 1k tbn, 1k tbc
At least one output file must be specified
"""



def parseInfo(string):
    data = {}
    stream_video = re.compile("""Stream #\d:(?P<index>\d+).*: (?P<type>\w+): (?P<codec>[a-zA-Z0-9\. \(\)\/]+), (?P<pixel_format>\w+), (?P<width>\d+)x(?P<height>\d+)""")
    stream_audio = re.compile("""Stream #\d:(?P<index>\d+).*: (?P<type>\w+): (?P<codec>[a-zA-Z0-9\. \(\)\/\[\]]+), (?P<hertz>\d+) Hz, .*, .*, (?P<bitrate>\d+) kb/s$""")
    input_ = re.compile(""" '([a-zA-Z0-9\. ]+)':$""")
    duration = re.compile("""Duration: (?P<duration>\d+:\d+:\d+.\d+), start: (?P<start>\d+.\d+), bitrate: (?P<bitrate>\d+) kb/s$""")

    for n in string.split('\n'):
        n = n.strip()
        if n.startswith('Input'):
            data['name'] = input_.findall(n)[0]
        elif n.startswith('Duration'):
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

if __name__ == '__main__':
    data = parseInfo(s3)
    scrub = 60
    m, s = divmod(scrub, 60)
    h, m = divmod(m, 60)
    scrubstr = "%02d:%02d:%02d" % (h, m, s)
    pprint(data)