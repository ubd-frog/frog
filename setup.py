#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='django-frog',
    description='Media server built on django',
    long_description=('A server and client solution to viewing '
                      ' and filtering large image and video collections'),
    version='1.0.6',
    author='Brett Dixon',
    author_email='theiviaxx@gmail.com',
    license='MIT',
    url='https://github.com/theiviaxx/frog',
    platforms='any',
    install_requires=['Django >=1.6', 'South >=0.7', 'django-haystack >=2.0.0'],
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
