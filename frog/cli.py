#!/usr/bin/env python
# -*- coding: utf-8 -*-
##################################################################################################
# Copyright (c) 2012 Brett Dixon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##################################################################################################


# check for venv and warn
# check for dev project: prompt for overwrite
# copy project dir
# generate secret_key.txt
# create static dir
# run migrate
# run createsuperuser
# print further instructions

import os
import argparse
import warnings
import sys
import subprocess
import logging
import random

import path

logging.basicConfig()

BASE = path.Path(os.path.abspath(__file__)).parent.parent
ENV = path.Path(os.getenv('VIRTUAL_ENV', os.getcwd()))
LOGGER = logging.getLogger('Frog Init')
LOGGER.setLevel(logging.INFO)


def isVirtualEnv():
    return 'VIRTUAL_ENV' in os.environ


def projectCheck():
    """checks to see if the project exists and propmts for overwrite"""
    project = ENV / 'dev'
    return project.exists()


def quickstart():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite everything without prompts')

    args, opts = parser.parse_known_args()

    if not isVirtualEnv():
        LOGGER.error('Please use a virtual environment')
        sys.exit()

    if not args.force:
        if not projectCheck():
            sys.exit()

    project = BASE / 'project' / 'dev'
    dest = ENV / 'dev'
    LOGGER.info('{} > {}'.format(project, dest))
    if dest.exists():
        dest.rmtree()
    project.copytree(dest)

    try:
        (dest / 'static').mkdir()
    except (OSError, IOError):
        pass

    os.chdir(dest)

    if not os.path.exists('secret_key.txt'):
        LOGGER.info('Generating secret key...')
        with open('secret_key.txt', 'w+') as fh:
            key = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
            fh.write(key)

    LOGGER.info('Running migrations...')
    subprocess.check_call(['python', 'manage.py', 'migrate'])
    LOGGER.info('Creating super user...')
    subprocess.check_call(['python', 'manage.py', 'createsuperuser'])
    subprocess.check_call(['python', 'manage.py', 'loaddata', '--app', 'frog', 'initial_data.json'])

    LOGGER.info('Generating nginx conf file...')
    conf = dest / 'frog.conf'
    conf.write_text((project.parent / 'frog.conf').text().format(
        static=(dest / 'static').replace('\\', '/'),
        ng=(project.parent / 'dist').replace('\\', '/'),
        env=dest.replace('\\', '/')
    ))
    (project.parent / 'mime.types').copy(dest)
    LOGGER.info(dest / 'frog.conf')

    LOGGER.info('Done')
