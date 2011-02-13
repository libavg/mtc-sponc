#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='Sponc',
    version='1.0',
    author='Martin Heisterman',
    author_email='mh@lulzmeister.de',
    url='http://www.sponc.de/',
    license='GPL',
    packages=['sponc'],
    scripts=['scripts/sponc'],
    package_data={
            'sponc': ['media/*.png', 'media/Sound/*.wav', 'media/Sound/scsyndefs/*',
                    'fonts/*'],
    }
)

