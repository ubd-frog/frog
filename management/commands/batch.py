""" batch """

import datetime
import json
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from frog.models import Gallery, RSSStorage


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dirnames', '-d',
            action='store_true',
            dest='dirnames',
            default=False,
            help='Use folder names as tags'
        ),
        make_option('--topdir', '-t',
            dest='topdir',
            default='/',
            help='Folder name to stop gathering tags from'
        ),
    )

    def handle(self, *args, **kwargs):
        pass