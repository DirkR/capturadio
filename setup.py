#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from capturadio import version_string as capturadio_version

with open('README.md') as f:
    readme = f.read()

setup(
    name='capturadio',
    version=capturadio_version,
    description="""CaptuRadio is a tool to record shows from internet
    radio stations to your computer or server.""",
    author='Dirk Ruediger',
    author_email='dirk@niebegeg.net',
    url='https://github.com/dirkr/capturadio',
    long_description=readme,
    classifiers=[
        "Topic :: Internet",
        "Topic :: Multimedia",
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "License :: Freeware",
    ],
    install_requires=[
        'PyRSS2Gen>=1.1',
        'docopt>=0.6',
        'mutagen>=1.21',
        'pytest>=2.3',
    ],
    packages=find_packages(exclude=('tests', 'docs', 'examples')),
    scripts=["recorder.py"],
    test_suite='tests',
)