#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os
from pip.req import parse_requirements

install_reqs = parse_requirements(os.path.abspath(os.path.dirname(__file__)) + '/requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='django-frog',
    description='Media server built on django',
    long_description='A server solution to viewing and filtering large image and video collections',
    version='2.0.0',
    author='Brett Dixon',
    author_email='theiviaxx@gmail.com',
    license='MIT',
    url='https://github.com/theiviaxx/frog',
    platforms='any',
    install_requires=reqs,
    packages=[
        'frog',
        'frog.views',
        'frog.management',
        'frog.management.commands',
        'frog.templatetags',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
    ],
    zip_safe=False,
    include_package_data=True
)
