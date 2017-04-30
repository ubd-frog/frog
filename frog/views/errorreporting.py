from __future__ import unicode_literals

import os
import re
import sys
from pprint import pformat

from django.template import Template, Context
from django.core.mail import mail_admins

import six


def linebreak_iter(template_source):
    """An iterator for a template string that yields on line breaks"""
    yield 0
    p = template_source.find('\n')
    while p >= 0:
        yield p + 1
        p = template_source.find('\n', p + 1)
    yield len(template_source) + 1


def report(title='Unhandled Exception', exec_info=(), **kwargs):
    """
    Create a technical server error response. The last three arguments are
    the values returned from sys.exc_info() and friends.

    :param title: Title of error email
    :type title: str
    :param exec_info: exc_info from traceback
    """

    exc_type, exc_value, tb = exec_info or sys.exc_info()
    reporter = ExceptionReporter(exc_type, exc_value, tb)
    html = reporter.get_traceback_html(**kwargs)

    mail_admins(title, 'html only', html_message=html)


class ExceptionReporter(object):
    """
    A class to organize and coordinate reporting on exceptions.
    """
    def __init__(self, exc_type, exc_value, tb):
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.tb = tb

        self.template_info = None
        self.template_does_not_exist = False
        self.loader_debug_info = None

        # Handle deprecated string exceptions
        if isinstance(self.exc_type, six.string_types):
            self.exc_value = Exception('Deprecated String Exception: %r' % self.exc_type)
            self.exc_type = type(self.exc_value)

    def get_traceback_data(self):
        """Return a dictionary containing traceback information."""
        default_template_engine = None

        if default_template_engine is None:
            template_loaders = []

        frames = self.get_traceback_frames()
        for i, frame in enumerate(frames):
            if 'vars' in frame:
                frame_vars = []
                for k, v in frame['vars']:
                    v = pformat(v)
                    # The escape filter assume unicode, make sure that works
                    if isinstance(v, six.binary_type):
                        v = v.decode('utf-8', 'replace')  # don't choke on non-utf-8 input
                    # Trim large blobs of data
                    if v and len(v) > 4096:
                        v = '%s... <trimmed %d bytes string>' % (v[0:4096], len(v))
                    frame_vars.append((k, v))
                frame['vars'] = frame_vars
            frames[i] = frame

        unicode_hint = ''
        if self.exc_type and issubclass(self.exc_type, UnicodeError):
            start = getattr(self.exc_value, 'start', None)
            end = getattr(self.exc_value, 'end', None)
            if start is not None and end is not None:
                unicode_str = self.exc_value.args[1]

        c = {
            'is_email': False,
            'frames': frames,
            'sys_executable': sys.executable,
            'sys_version_info': '%d.%d.%d' % sys.version_info[0:3],
            'sys_path': sys.path,
        }

        # Check whether exception info is available
        if self.exc_type:
            c['exception_type'] = self.exc_type.__name__
        if self.exc_value:
            c['exception_value'] = self.exc_value
        if frames:
            c['lastframe'] = frames[-1]
        return c

    def get_traceback_html(self, **kwargs):
        "Return HTML version of debug 500 HTTP error page."
        t = Template(TECHNICAL_500_TEMPLATE)
        c = self.get_traceback_data()
        c['kwargs'] = kwargs
        return t.render(Context(c))

    def _get_lines_from_file(self, filename, lineno, context_lines, loader=None, module_name=None):
        """
        Returns context_lines before and after lineno from file.
        Returns (pre_context_lineno, pre_context, context_line, post_context).
        """
        source = None
        if loader is not None and hasattr(loader, "get_source"):
            try:
                source = loader.get_source(module_name)
            except ImportError:
                pass
            if source is not None:
                source = source.splitlines()
        if source is None:
            try:
                with open(filename, 'rb') as fp:
                    source = fp.read().splitlines()
            except (OSError, IOError):
                pass
        if source is None:
            return None, [], None, []

        # If we just read the source from a file, or if the loader did not
        # apply tokenize.detect_encoding to decode the source into a Unicode
        # string, then we should do that ourselves.
        if isinstance(source[0], six.binary_type):
            encoding = 'ascii'
            for line in source[:2]:
                # File coding may be specified. Match pattern from PEP-263
                # (http://www.python.org/dev/peps/pep-0263/)
                match = re.search(br'coding[:=]\s*([-\w.]+)', line)
                if match:
                    encoding = match.group(1).decode('ascii')
                    break
            source = [six.text_type(sline, encoding, 'replace') for sline in source]

        lower_bound = max(0, lineno - context_lines)
        upper_bound = lineno + context_lines

        pre_context = source[lower_bound:lineno]
        context_line = source[lineno]
        post_context = source[lineno + 1:upper_bound]

        return lower_bound, pre_context, context_line, post_context

    def get_traceback_frames(self):
        """Returns the traceback frames as a list"""
        frames = []
        tb = self.tb
        while tb is not None:
            # Support for __traceback_hide__ which is used by a few libraries
            # to hide internal frames.
            if tb.tb_frame.f_locals.get('__traceback_hide__'):
                tb = tb.tb_next
                continue
            filename = tb.tb_frame.f_code.co_filename
            function = tb.tb_frame.f_code.co_name
            lineno = tb.tb_lineno - 1
            loader = tb.tb_frame.f_globals.get('__loader__')
            module_name = tb.tb_frame.f_globals.get('__name__') or ''
            pre_context_lineno, pre_context, context_line, post_context = self._get_lines_from_file(
                filename, lineno, 7, loader, module_name,
            )
            if pre_context_lineno is not None:
                frames.append({
                    'tb': tb,
                    'type': 'django' if module_name.startswith('django.') else 'user',
                    'filename': filename,
                    'function': function,
                    'lineno': lineno + 1,
                    'vars': list(six.iteritems(tb.tb_frame.f_locals)),
                    'id': id(tb),
                    'pre_context': pre_context,
                    'context_line': context_line,
                    'post_context': post_context,
                    'pre_context_lineno': pre_context_lineno + 1,
                })
            tb = tb.tb_next

        return frames

    def format_exception(self):
        """
        Return the same data as from traceback.format_exception.
        """
        import traceback
        frames = self.get_traceback_frames()
        tb = [(f['filename'], f['lineno'], f['function'], f['context_line']) for f in frames]
        list = ['Traceback (most recent call last):\n']
        list += traceback.format_list(tb)
        list += traceback.format_exception_only(self.exc_type, self.exc_value)
        return list

#
# Templates are embedded in the file so that we know the error handler will
# always work even if the template loader is broken.
#

TECHNICAL_500_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <meta name="robots" content="NONE,NOARCHIVE">
  <title>{% if exception_type %}{{ exception_type }}{% else %}Report{% endif %}</title>
</head>
<body style="padding: 0;margin: 0;font: small sans-serif;">
<div id="summary" style="padding: 10px 20px;margin: 0;border-bottom: 1px solid #ddd;background: #ffc;">
  <h1 style="padding: 0;margin: 0;font-weight: normal;">{% if exception_type %}{{ exception_type }}{% else %}Report{% endif %}</h1>
  <pre class="exception_value" style="padding: 0;margin: 10px 0 10px 0;font-size: 1.5em;white-space: pre-wrap;font-family: sans-serif;color: #666;">{% if exception_value %}{{ exception_value|escape }}{% else %}No exception message supplied{% endif %}</pre>
  <table class="meta" style="padding: 0;margin: 0;border: none;border-collapse: collapse;width: 100%;background: transparent;">
{% if exception_type %}
    <tr style="padding: 0;margin: 0;">
      <th style="padding: 0;margin: 0;">Exception Type:</th>
      <td style="padding: 0;margin: 0;">{{ exception_type }}</td>
    </tr>
{% endif %}
{% if exception_type and exception_value %}
    <tr style="padding: 0;margin: 0;">
      <th style="padding: 0;margin: 0;">Exception Value:</th>
      <td style="padding: 0;margin: 0;"><pre style="padding: 0;margin: 0;font-size: 100%;white-space: pre-wrap;">{{ exception_value|escape }}</pre></td>
    </tr>
{% endif %}
{% if lastframe %}
    <tr style="padding: 0;margin: 0;">
      <th style="padding: 0;margin: 0;">Exception Location:</th>
      <td style="padding: 0;margin: 0;">{{ lastframe.filename|escape }} in {{ lastframe.function|escape }}, line {{ lastframe.lineno }}</td>
    </tr>
{% endif %}
    <tr style="padding: 0;margin: 0;">
      <th style="padding: 0;margin: 0;">Python Executable:</th>
      <td style="padding: 0;margin: 0;">{{ sys_executable|escape }}</td>
    </tr>
    <tr style="padding: 0;margin: 0;">
      <th style="padding: 0;margin: 0;">Python Version:</th>
      <td style="padding: 0;margin: 0;">{{ sys_version_info }}</td>
    </tr>
    <tr style="padding: 0;margin: 0;">
      <th style="padding: 0;margin: 0;">Python Path:</th>
      <td style="padding: 0;margin: 0;"><pre style="padding: 0;margin: 0;font-size: 100%;white-space: pre-wrap;">{{ sys_path }}</pre></td>
    </tr>
    {% for key, value in kwargs.items %}
    <tr style="padding: 0;margin: 0;">
      <th style="padding: 0;margin: 0;">{{key}}</th>
      <td style="padding: 0;margin: 0;"><pre style="padding: 0;margin: 0;font-size: 100%;white-space: pre-wrap;">{{ value }}</pre></td>
    </tr>
    {% endfor %}
  </table>
</div>
{% if frames %}
<div id="traceback" style="padding: 10px 20px;margin: 0;border-bottom: 1px solid #ddd;background: #eee;">
  <h2 style="padding: 0;margin: 0;margin-bottom: .8em;">Traceback</h2>
  <div id="browserTraceback" style="padding: 0;margin: 0;">
    <ul class="traceback" style="padding: 0;margin: 0;list-style-type: none;color: #222;">
      {% for frame in frames %}
        <li class="frame {{ frame.type }}" style="padding: 0;margin: 0;padding-bottom: 1em;color: #000;background-color: #e0e0e0;">
          <code style="padding: 0;margin: 0;font-size: 100%;white-space: pre-wrap;">{{ frame.filename|escape }}</code> in <code style="padding: 0;margin: 0;font-size: 100%;white-space: pre-wrap;">{{ frame.function|escape }}</code>

          {% if frame.context_line %}
            <div class="context" id="c{{ frame.id }}" style="padding: 10px 0;margin: 0;overflow: hidden;">
              {% if frame.pre_context and not is_email %}
                <ol start="{{ frame.pre_context_lineno }}" class="pre-context" id="pre{{ frame.id }}" style="padding: 0;margin: 0 10px;padding-left: 30px;list-style-position: inside;">
                {% for line in frame.pre_context %}
                  <li style="padding: 0;margin: 0;font-family: monospace;white-space: pre;color: #666;cursor: pointer;">
                      <pre style="padding: 0;margin: 0;font-size: 100%;white-space: pre-wrap;display: inline;">
{{ line|escape }}
                      </pre>
                  </li>
                {% endfor %}
                </ol>
              {% endif %}
              <ol start="{{ frame.lineno }}" class="context-line" style="padding: 0;margin: 0 10px;padding-left: 30px;list-style-position: inside;">
                <li style="padding: 0;margin: 0;font-family: monospace;white-space: pre;color: #000;background-color: #bbb;">
                    <pre style="padding: 0;margin: 0;font-size: 100%;white-space: pre-wrap;display: inline;">
{{ frame.context_line|escape }}
                    </pre>
                </li>
              </ol>
              {% if frame.post_context %}
                <ol start='{{ frame.lineno }}' class="post-context" id="post{{ frame.id }}" style="padding: 0;margin: 0 10px;padding-left: 30px;list-style-position: inside;">
                  {% for line in frame.post_context %}
                  <li style="padding: 0;margin: 0;font-family: monospace;white-space: pre;color: #000;background-color: #bbb;">
                      <pre style="padding: 0;margin: 0;font-size: 100%;white-space: pre-wrap;display: inline;">
{{ line|escape }}
                      </pre>
                  </li>
                  {% endfor %}
              </ol>
              {% endif %}
            </div>
          {% endif %}

          {% if frame.vars %}
            <div class="commands" style="padding: 0;margin: 0;margin-left: 40px;">
                <h2 style="padding: 0;margin: 0;margin-bottom: .8em;">Local Vars</h2>
            </div>
            <table class="vars" id="v{{ frame.id }}" style="padding: 0;margin: 5px 0 2px 40px;border: 1px solid #ccc;border-collapse: collapse;width: 100%;background: white;">
              <thead style="padding: 0;margin: 0;">
                <tr style="padding: 0;margin: 0;">
                  <th style="padding: 1px 6px 1px 3px;margin: 0;background: #fefefe;text-align: left;font-weight: normal;font-size: 11px;border: 1px solid #ddd;">Variable</th>
                  <th style="padding: 1px 6px 1px 3px;margin: 0;background: #fefefe;text-align: left;font-weight: normal;font-size: 11px;border: 1px solid #ddd;">Value</th>
                </tr>
              </thead>
              <tbody style="padding: 0;margin: 0;">
                {% for var in frame.vars %}
                  <tr style="padding: 0;margin: 0;">
                    <td style="padding: 2px 3px;margin: 0;vertical-align: top;font-family: monospace;">{{ var.0|escape }}</td>
                    <td class="code" style="padding: 2px 3px;margin: 0;vertical-align: top;font-family: monospace;width: 100%;"><pre style="padding: 0;margin: 0;font-size: 100%;white-space: pre-wrap;overflow: hidden;">{{ var.1 }}</pre></td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          {% endif %}
        </li>
      {% endfor %}
    </ul>
  </div>
</div>
{% endif %}
</body>
</html>
"""
