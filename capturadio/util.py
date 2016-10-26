"""capturadio is a library to capture mp3 radio streams, process
the recorded media files and generate an podcast-like rss feed.

 * http://github.com/dirkr/capturadio
 * Repository and issue-tracker: https://github.com/dirkr/capturadio
 * Licensed under the public domain
 * Copyright (c) 2012- Dirk Ruediger <dirk@niebegeg.net>

The module capturadio.util provides some helper funtions.
"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import unicodedata
import re
import time
import urllib.parse as urlparse
import urllib.parse as urllib
import logging
import shutil

from mutagenx.mp3 import MP3
from xdg import XDG_CONFIG_HOME


def format_date(pattern, time_value):
    if type(time_value).__name__ == 'float':
        time_value = time.localtime(time_value)
    elif type(time_value).__name__ == 'struct_time':
        pass
    else:
        raise TypeError(
            'time_value has to be a struct_time or a float. "%s" given.' %
            time_value
        )
    return time.strftime(pattern, time_value)


def parse_duration(duration_string):
    pattern = r"((?P<d>\d+)d)?((?P<h>\d+)h)?((?P<m>\d+)m)?((?P<s>\d+)s?)?"
    matches = re.match(pattern, duration_string)
    (d, h, m, s) = (
        matches.group('d'),
        matches.group('h'),
        matches.group('m'),
        matches.group('s')
    )
    duration = \
        (int(d) * 24*3600 if d is not None else 0) +\
        (int(h) * 3600 if h is not None else 0) +\
        (int(m) * 60 if m is not None else 0) +\
        (int(s) if s is not None else 0)
    return duration


# Taken from http://stackoverflow.com/questions/120951/how-can-i-normalize-a-url-in-python
def url_fix(s, charset='utf-8'):
    """Sometimes you get an URL by a user that just isn't a real
    URL because it contains unsafe characters like ' ' and so on.  This
    function can fix some of the problems in a similar way browsers
    handle data entered by the user:

    :param charset: The target charset for the URL if the url was
                    given as unicode string.
    """
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = urllib.quote(path, '/%')
    qs = urllib.quote_plus(qs, ':&=')
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))


# taken from http://stackoverflow.com/a/295466/981739
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub('[-,;\s]+', '_', value.decode()).strip().lower()
    return value


def find_configuration():
    xdg_location = os.path.join(XDG_CONFIG_HOME, 'capturadio')
    legacy_locations = [
        os.path.join(os.getcwd(), 'capturadiorc'),
        os.path.expanduser('~/.capturadio/capturadiorc'),
        os.path.expanduser('~/.capturadiorc'),
    ]
    for location in legacy_locations:
        if os.path.exists(location):
            if not os.path.exists(xdg_location):
                shutil.copy(location, xdg_location)
                logging.info("Copy legacy configuration file {} to {}."
                             .format(location, xdg_location))
            logging.warning("Legacy configuration file {} can be removed."
                            .format(location))

    config_locations = [
        xdg_location,
        '/etc/capturadiorc',
    ]
    for location in config_locations:
        if os.path.exists(location):
            return location
    return os.path.join(XDG_CONFIG_HOME, 'capturadio')


def migrate_mediafile_to_episode(config, filename, show):
    from datetime import datetime, date, timedelta
    from capturadio import Episode

    logging.info("Migrate {} to episode".format(filename))
    episode = Episode(config, show)
    audiofile = MP3(filename)
    episode.filename = filename
    episode.duration = round(float(_get_mp3_tag(audiofile, 'TLEN', 0)) / 1000)
    episode.duration_string = str(timedelta(seconds=episode.duration))
    filemtime = date.fromtimestamp(
        os.path.getmtime(filename)).strftime('%Y-%m-%d %H:%M')
    starttimestr = _get_mp3_tag(audiofile, 'TDRC', filemtime)
    episode.starttime = datetime.strptime(
        starttimestr,
        '%Y-%m-%d %H:%M'
    ).timetuple()
    episode.pubdate = time.strftime('%c', episode.starttime)
    episode.slug = os.path.join(
        show.slug,
        "{}_{}.mp3".format(
            slugify(episode.show.id),
            time.strftime('%Y-%m-%d_%H-%M', episode.starttime)
        )
    )
    basename = os.path.basename(filename)
    episode.name = _get_mp3_tag(audiofile, 'TIT2', basename[:-4])
    new_filename = os.path.join(show.filename, basename)
    if new_filename != filename:
        new_dirname = os.path.dirname(new_filename)
        if not os.path.exists(new_dirname):
            os.makedirs(new_dirname)
        shutil.move(filename, new_filename)
        episode.filename = new_filename
    episode.slug = os.path.join(show.slug, basename)
    episode.filesize = str(os.path.getsize(episode.filename))
    episode.mimetype = 'audio/mpeg'
    return episode


def _get_mp3_tag(audiofile, tag_string, default):
    """Helper function to get the contents of an ID3 tag from an audiofile."""
    try:
        return "{}".format(audiofile[tag_string])
    except (KeyError, TypeError):
        return default
