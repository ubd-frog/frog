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

import re

RE_VIDEO = re.compile("""Stream #\d[:.](?P<index>\d+).*: (?P<type>\w+): (?P<codec>.*), (?P<pixel_format>[\w\(\)]+), (?P<width>\d+)x(?P<height>\d+)""")
RE_AUDIO = re.compile("""Stream #\d[:.](?P<index>\d+).*: (?P<type>\w+): (?P<codec>.*), (?P<hertz>\d+) Hz, .*, .*, (?P<bitrate>\d+) kb/s""")
RE_DURATION = re.compile("""Duration: (?P<duration>\d+:\d+:\d+.\d+), start: (?P<start>\d+.\d+), bitrate: (?P<bitrate>\d+) kb/s$""")


def parseInfo(strings):
    data = {}

    for n in strings:
        n = n.strip()
        if n.startswith('Duration'):
            r = RE_DURATION.search(n)
            data.update(r.groupdict())
        elif n.startswith('Stream'):
            if 'Video' in n:
                data.setdefault('video', [])
                r = RE_VIDEO.search(n)
                data['video'].append(r.groupdict())
            elif 'Audio' in n:
                data.setdefault('audio', [])
                r = RE_AUDIO.search(n)
                data['audio'].append(r.groupdict())

    return data