#!/usr/bin/env python3
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
        "Programming Language :: Python :: 3",
        "License :: Freeware",
    ],
    install_requires=[
        'xdg>=5.0.0',
        'Jinja2>=2.10.1',
        'docopt>=0.6.1',
        'MarkupSafe>=1.0.0',
        'mutagenx>=1.24',
        'pytest>=2.3.5',
        'py>=1.10.0',
    ],
    packages=find_packages(exclude=('docs', 'examples')),
    include_package_data = True,
    package_data = {
        '': ['*.txt', '*.md'],
        'capturadio': ['templates/*.jinja2'],
    },
    entry_points = {
        'console_scripts': [
            'recorder = capturadio.recorder_cli:main'
        ],
    },
    test_suite='tests',
)