"""capturadio is a library to capture mp3 radio streams, process
the recorded media files and generate an podcast-like rss feed.

 * http://github.com/dirkr/capturadio
 * Repository and issue-tracker: https://github.com/dirkr/capturadio
 * Licensed under the public domain
 * Copyright (c) 2012- Dirk Ruediger <dirk@niebegeg.net>

The module capturadio.rss provides classes to generate RSS streams.
"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime as dt
import os
import time
import logging
import jinja2
import urllib.parse as urllib
from mutagenx.mp3 import MP3, HeaderNotFoundError

from capturadio import Configuration, version_string as capturadio_version
from capturadio.util import url_fix, format_date


class Audiofile(object):
    """
    A class to store metadata of a media file.
    """

    def __init__(self, filename):
        self.filename = filename
        self.config = Configuration()
        self.path = filename
        self.filesize = str(os.path.getsize(filename))
        self.basename = os.path.basename(filename)
        local_path = self.path.replace(self.config.destination, '')
        self.url = self.config.feed['base_url'] + url_fix(local_path)
        try:
            audio = MP3(self.path)
            self.extract_metadata(audio)
        except HeaderNotFoundError:
            logging.error("Couldn't find MPEG header in file %r" % self.path)
        self.size = os.path.getsize(self.path)
        self.pubdate = dt.datetime.fromtimestamp(os.path.getmtime(self.path))

    def extract_metadata(self, audiofile):
        """
        Extract the ID3 tags of the file 'audiofile' and store them as object
        attributes.
        """

        self.title = self._get_tag(audiofile, 'TIT2', self.basename[:-4])
        self.show = self._get_tag(audiofile, 'TALB', None)
        if self.show is None:
            self.show = self.basename[:-4]
        else:
            """Fixed for Unicode output"""
            for s in self.config.shows.values():
                if str(s.name) == self.show:
                    self.link = s.link_url
                    break
        default_date = format_date(self.config.date_pattern, time.time())
        self.date = self._get_tag(audiofile, 'TDRC', default_date)
        self.artist = self._get_tag(audiofile, 'TPE1', self.show)
        __playtime = self._get_tag(audiofile, 'TLEN', None)
        if __playtime is not None:
            self.playtime = int(__playtime) / 1000
        else:
            self.playtime = 0
        self.copyright = self._get_tag(
            audiofile,
            'TCOP',
            self.artist
        )
        __description = u'Show: %s<br>Episode: %s<br>Copyright: %s %s' % (
            self.show, self.title, self.date[:4], self.copyright)
        self.description = self._get_tag(
            audiofile,
            "COMM:desc:'eng'",
            __description
        )
        self.link = self._get_tag(
            audiofile,
            "TCOM",
            u'http://www.podcast.de/'
        )

    def _get_tag(self, audiofile, tag_string, default):
        """
        Helper function to get the contents of an ID3 tag from an audiofile.
        """
        try:
            return u"%s" % audiofile[tag_string]
        except (KeyError, TypeError):
            return default


class RssImage(object):
    url = None
    title = None
    link = None
    description = None


class RssFeed(object):
    """
    A collection of audiofiles and some metadata, used as the basis for the
    generation of the rss feed.
    """

    files_cache = {}
    items = []
    generator = 'CaptuRadio v%s' % capturadio_version
    link = 'http://www.podcast.de/'

    def __init__(self, root_path, local_path, config):
        logging.debug('create RssFeed in {}'.format(local_path))

        self.pubdate = dt.datetime.fromtimestamp(time.time())
        self.root_path = root_path
        self.path = local_path
        self.title = config.feed['title']
        if (local_path != ''):
            self.title += " - " + local_path.replace('/', ' - ')

        self.link = config.feed['about_url']
        self.description = config.feed['description']
        self.language = config.feed['language']
        self.basename = config.feed['filename']

        self.urlbase = config.feed['base_url']
        if local_path is not '':
            self.urlbase += urllib.quote(local_path)

        if not self.urlbase.endswith('/'):
            self.urlbase += '/'

        self.image = {
            'url' : config.feed['default_logo_url'],
            'description' : "{}\n\nLogo: {}".format(
                config.feed['description'],
                config.feed['logo_copyright'],
            ),
        }

    def write_to_file(self):
        """
        Write the list of files as RSS formatted file.

        The argument 'path' points to the folder, where the file will
        be written to. The name of the file is specified in
        config.feed['filename'] and defaults to 'rss.xml'.
        """
        if len(self.items) > 0:
            filename = os.path.join(self.root_path, self.path, self.basename)
            this_dir = os.path.dirname(os.path.abspath(__file__))
            templates_dir = os.path.join(this_dir, 'templates')
            j2_env = jinja2.Environment(
                loader = jinja2.FileSystemLoader(templates_dir),
                trim_blocks=True,
            )
            contents = j2_env.get_template('feed.xml.jinja').render(feed=self)
            with open(filename, "w") as rssfile:
                rssfile.write(contents)

    def read_folder(self):
        """Helper function to read collect the audiofiles contained in
        the folder specified with the argument 'dirname'.
        """
        foldername = os.path.join(self.root_path, self.path)
        logging.info(u'_read_folder: processing %s' % foldername)

        for dir, dirs, files in os.walk(foldername):
            for filename in files:
                path = os.path.join(dir, filename)
                if os.path.exists(path) and \
                    os.path.isfile(path) and \
                        path.endswith(".mp3"):
                    self.items.append(self._get_audiofile(path))

    def _get_audiofile(self, path):
        logging.info(u'Enter _get_audiofile(%s)' % path)
        if path not in RssFeed.files_cache.keys():
            audio_file = Audiofile(path)
            RssFeed.files_cache[path] = audio_file
        else:
            audio_file = RssFeed.files_cache[path]
        return audio_file

    def _get_link_url(self, station_name):
        for id, station in self.config.stations.items():
            if station_name == station.name:
                return station.link_url
        return None

    def _get_logo_url(self, station_name):
        for id, station in self.config.stations.items():
            if station_name == station.name:
                return station.logo_url
        return None