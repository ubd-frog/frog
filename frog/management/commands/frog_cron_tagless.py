##################################################################################################
# Copyright (c) 2016 Brett Dixon
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


from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count

from frog.models import Gallery, Image, Tag, FROG_SITE_URL


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        main = Gallery.objects.get(pk=1)
        mapping = {}

        images = main.images.annotate(num_tags=Count('tags')).filter(num_tags__lte=1)
        videos = main.images.filter(tags__isnull=True)

        items = list(images) + list(videos)
        for item in items:
            mapping.setdefault(item.author, [])
            linktype = 'image' if isinstance(item, Image) else 'video'
            item.link = '{}/frog/{}/{}'.format(FROG_SITE_URL, linktype, item.id)
            mapping[item.author].append(item)

        for author, items in mapping.iteritems():
            items = list(set(items))
            authortag = Tag.objects.filter(artist=True, name=author.get_full_name())
            if not authortag:
                self.stderr.write('No tag forund for {}'.format(author))
                continue
            link = '{}/frog/gallery/1#{{%22filters%22:[[{}],[0],[]]}}'.format(FROG_SITE_URL, authortag[0].id)
            html = render_to_string(
                'frog/cron_email_tagless.html',
                {'items': items, 'SITE_URL': FROG_SITE_URL, 'gallery': main, 'link': link}
            )
            subject = 'Tagless Items'
            from_email = settings.DEFAULT_FROM_EMAIL
            to = author.email
            text_content = 'Only html supported'
            send_mail(subject, text_content, from_email, [to], html_message=html)
            self.stdout.write('Emailed {} for {} items'.format(author.email, len(items)))
