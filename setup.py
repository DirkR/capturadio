# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from capturadio import version_string as capturadio_version

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='capturadio',
    version=capturadio_version,
    description='CaptuRadio is a tool to record shows from internet radio stations to your computer or server.',
    long_description=readme,
    author='Dirk Ruediger',
    author_email='dirk@niebegeg.net',
    url='https://github.com/dirkr/capturadio',
    license=license,
    packages=find_packages(exclude=('tests', 'docs', 'examples'))
)