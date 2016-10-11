"""capturadio is a library to capture mp3 radio streams, process
the recorded media files and generate an podcast-like rss feed.

 * http://github.com/dirkr/capturadio
 * Repository and issue-tracker: https://github.com/dirkr/capturadio
 * Licensed under the public domain
 * Copyright (c) 2012- Dirk Ruediger <dirk@niebegeg.net>

"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from xdg import XDG_DATA_HOME

from capturadio.entities import Station, Show, Episode
from capturadio.recorder import Recorder
from capturadio.config import Configuration
from capturadio.util import format_date, slugify, parse_duration

version = (0, 10, 0)
version_string = ".".join(map(str, version))

app_folder = os.path.join(XDG_DATA_HOME, 'capturadio')
if not os.path.exists(app_folder):
    os.makedirs(app_folder)