#!/usr/bin/env python2.7
# -*- coding: utf_8 -*-

import urllib2
import time
import argparse
import os
import logging
import re
import sys
import string

def format_date(pattern, time_value):
    if (type(time_value).__name__ == 'float'):
        time_value = time.localtime(time_value)
    elif (type(time_value).__name__ == 'struct_time'):
        pass
    else:
        raise TypeError('time_value has to be a struct_time or a float. "%s" given.' % time_value)
    return time.strftime(pattern, time_value)

class Configuration:
    filename = '~/.capturadio/capturadiorc'
    log = None

    def __init__(self):
        self.stations = {}
        self.shows = {}
        self.default_logo_url = None
        self.destination = os.getcwd()
        self.date_pattern = "%Y-%m-%d %H:%M"
        self.log = logging.getLogger('capturadio.Configuration')
        self.feed = {}
        self.__load_config()

    def __load_config(self):
        import ConfigParser
        config = ConfigParser.ConfigParser()
        config.read([os.path.expanduser(Configuration.filename)])

        if config.has_section('settings'):
            self.set_destination(config.get('settings', 'destination', os.getcwd()))
            if config.has_option('settings', 'date_pattern'):
                self.date_pattern = os.path.expanduser(config.get('settings', 'date_pattern'))
        self._read_feed_settings(config)
        self._add_stations(config)

    def _read_feed_settings(self, config):
        if config.has_section('feed'):
            if config.has_option('feed', 'default_logo_url'):
                self.default_logo_url = config.get('feed', 'default_logo_url')
            self.feed['base_url'] = config.get('feed', 'url')
            if not self.feed['base_url'].endswith('/'):
                self.feed['base_url'] += '/'
            self.feed['title'] = config.get('feed', 'title', 'Internet Radio Recordings')
            self.feed['about_url'] = config.get('feed', 'about_url', 'http://my.example.org/about.html')
            self.feed['description'] = config.get('feed', 'description', 'Recordings')
            self.feed['language'] = config.get('feed', 'language', 'en')
            self.feed['file_name'] = config.get('feed', 'filename', 'rss.xml')
            self.feed['logo_copyright'] = config.get('feed', 'default_logo_copyright', None)

        # Read stations
    def _add_stations(self, config):
        if config.has_section('stations'):
            for station_id in config.options('stations'):
                station_stream = config.get('stations', station_id)
                station_name = station_id
                station_url = self.default_logo_url
                station_logo_url = self.default_logo_url
                if config.has_section(station_id):
                    if config.has_option(station_id, 'name'):
                        station_name = config.get(station_id, 'name')
                    if config.has_option(station_id, 'logo_url'):
                        station_logo_url = config.get(station_id, 'logo_url')
                station = self.add_station(station_id, station_stream, station_name, station_logo_url)

                if config.has_option(station_id, 'link_url'):
                    station.link_url = config.get(station_id, 'link_url')
                else:
                    station.link_url = self.feed['base_url']

                self._add_shows(config, station)

    def _add_shows(self, config, station):
        if config.has_section(station.id) and config.has_option(station.id, 'shows'):
            show_ids = re.split(',? +', config.get(station.id, 'shows'))
            for show_id in show_ids:
                if config.has_section(show_id):
                    if config.has_option(show_id, 'title'):
                        show_title = config.get(show_id, 'title')
                    else:
                        raise Exception('No title option defined for show "%s".' % show_id)

                    if config.has_option(show_id, 'duration'):
                        show_duration = parse_duration(config.get(show_id, 'duration'))
                    else:
                        raise Exception('No duration option defined for show "%s".' % show_id)

                    if config.has_option(show_id, 'logo_url'):
                        show_logo_url = config.get(show_id, 'logo_url')
                    else:
                        show_logo_url = station.logo_url

                    show = self.add_show(station, show_id, show_title, show_duration, show_logo_url)

                    if config.has_option(show_id, 'link_url'):
                        show.link_url = config.get(show_id, 'link_url')
                    else:
                        show.link_url = station.link_url


    def set_destination(self, destination):
        if destination is not None:
            destination = os.path.expanduser(destination)
            if (os.path.exists(destination) and os.path.isdir(destination)):
                destination = os.path.realpath(os.path.abspath(os.path.expanduser(destination)))
                self.destination = unicode(destination)
            return self.destination

        raise Exception("Could not set destination %s" % destination)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    def get_station_ids(self):
        if self.stations is not None:
            return self.stations.keys()
        else:
            return None

    def add_station(self, id, stream_url, name = None, logo_url = None):
        station = Station(unicode(id, 'utf-8'), stream_url, unicode(name, 'utf-8'), logo_url)
        self.stations[id] = station
        return station

    def add_show(self, station, id, name, duration, logo_url = None):
        if not isinstance(station, Station):
            raise TypeError('station has to be of type "Station"')
        show = Show(station, id, name, duration, logo_url)
        self.log.info(u'station_id=%s, show_id=%s, name=%s' % (station.id, id, unicode(name)))
        self.shows[id] = show
        return show


class Station:
    """Describes a radio station, consists of shows."""

    def __init__(self, id, stream_url, name, logo_url = None):
        self.id = id
        self.name = name
        self.stream_url = stream_url
        self.logo_url = logo_url
        self.shows = []
        self.registry = None

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

class Show:
    """Describes a single show, consists of episodes and belongs to a station"""

    def __init__(self, station, id, name, duration, logo_url = None):
        if not isinstance(station, Station):
            raise TypeError('station has to be of type "Station"')

        self.station = station
        self.id = id
        self.name = name
        self.duration = duration
        self.logo_url = logo_url
        station.shows.append(self)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    def get_stream_url(self):
        return self.station.stream_url

class Recorder:
    log = None

    def __init__(self, config):
        logging.basicConfig(
            filename = os.path.expanduser('~/.capturadio/log'),
            level = logging.DEBUG,
        )
        self.log = logging.getLogger('capturadio')
        self.config = config
        self.start_time = None

    def capture(self, show):
        self.log.info(u'capture "%s" from "%s" for %s seconds to %s' % \
                (show.name, show.station.name, show.duration, config.destination))
        import tempfile
        self.start_time = time.time()
        try:
            file_name = u"%s/capturadio_%s.mp3" % (tempfile.gettempdir(), os.getpid())
            self._write_stream_to_file(show, file_name)
            file_name = self._copy_file_to_destination(show, file_name)
            self._add_metadata(show, file_name)
            self.start_time = None
        except Exception as e:
            message = "Could not complete capturing, because an exception occured.", e
            self.log.error(message, e.message)
            print message
            sys.exit(1)

    def _write_stream_to_file(self, show, file_name):
        not_ready = True
        try:
            file = open(file_name, 'w+b')
            stream = urllib2.urlopen(show.get_stream_url());
            while not_ready:
                file.write(stream.read(10240));
                if ((time.time() - self.start_time) > show.duration):
                    not_ready = False
            file.close
        except Exception as e:
            message = "Could not capture show, because an exception occured.", e
            self.log.error(message, e.message)
            print message
            os.remove(file_name)

    def _copy_file_to_destination(self, show, file_name):
        import shutil, re

        time_string = format_date(self.config.date_pattern, time.localtime(self.start_time))
        target_file = u"%s/%s/%s/%s_%s.mp3" % \
            (self.config.destination,
             show.station.name,
             show.name,
             show.name,
             time_string)
        target_file = re.compile(u'[^\w\d._/ -]').sub('', target_file)
        if (not os.path.isdir(os.path.dirname(target_file))):
            os.makedirs(os.path.dirname(target_file))
        try:
            shutil.copy2(file_name, target_file)
            return target_file
        except IOError, e:
            message = "Could not copy tmp file to %s." % target_file
            self.log.error(message, e.message)
            os.remove(file_name)
            raise IOError(message, e)

    def _add_metadata(self, show, file_name):
        if file_name is None:
            raise "file_name is not set - you cannot add metadata to None"

        from mutagen.mp3 import MP3
        import mutagen.id3
        year = time.strftime('%Y', time.localtime(self.start_time))
        time_string = format_date(self.config.date_pattern, time.localtime(self.start_time))
        episode_title = u'%s on %s' % (show.name, time_string)
        comment = u'Show: %s\nEpisode: %s\nCopyright: %s %s' % (show.name, episode_title, year, show.station.name)

        audio = MP3(file_name)
        # See http://www.id3.org/id3v2.3.0 for details about the ID3 tags
        audio["TIT2"] = mutagen.id3.TIT2(encoding=2, text=[episode_title])
        audio["TDRC"] = mutagen.id3.TDRC(encoding=2, text=[format_date(self.config.date_pattern, self.start_time)])
        audio["TCON"] = mutagen.id3.TCON(encoding=2, text=[u'Podcast'])
        audio["TALB"] = mutagen.id3.TALB(encoding=2, text=[show.name])
        audio["TLEN"] = mutagen.id3.TLEN(encoding=2, text=[duration * 1000])
        audio["TPE1"] = mutagen.id3.TPE1(encoding=2, text=[show.station.name])
        audio["TCOP"] = mutagen.id3.TCOP(encoding=2, text=[show.station.name])
        audio["COMM"] = mutagen.id3.COMM(encoding=2, text=[comment])
        self._add_logo(show, audio)
        audio.save()

    def _add_logo(self, show, audio):
        from mutagen.id3 import APIC
        # APIC part taken from http://mamu.backmeister.name/praxis-tipps/pythonmutagen-audiodateien-mit-bildern-versehen/
        url = show.station.logo_url
        if url is not None:
            request = urllib2.Request(url)
            request.get_method = lambda : 'HEAD'
            try:
                response = urllib2.urlopen(request)
                logo_type = response.info().gettype()

                if logo_type in ['image/jpeg', 'image/png']:
                    img_data  = urllib2.urlopen(url).read()
                    img = APIC(
                        encoding = 3, # 3 is for utf-8
                        mime = logo_type,
                        type = 3, # 3 is for the cover image
                        desc = u'Station logo',
                        data = img_data
                    )
                    audio.tags.add(img)
            except urllib2.HTTPError, e:
                message = "Error during capturing %s" % url
                self.log.error(message, e)
                print message, e

def parse_duration(duration_string):
#   pattern = r"^((?P<h>\d+h)(?iP<m>\d+m)?(?iP<s>\d+s)?|?P<ps>\d+)$"
    pattern = r"((?P<h>\d+)h)?((?P<m>\d+)m)?((?P<s>\d+)s?)?"
    matches = re.match(pattern, duration_string)
    (h, m, s) = (matches.group('h'), matches.group('m'), matches.group('s'))
    duration = (int(h) * 3600 if h != None else 0) + \
               (int(m) * 60 if m != None else 0) + \
               (int(s) if s != None else 0)
    return duration

if __name__ == "__main__":

    config = Configuration()

    if len(sys.argv) == 1:
        sys.argv.append('--help')

    parser = argparse.ArgumentParser(
        description='Capture internet radio programs broadcasted in mp3 encoding format.',
        epilog = "Here is a list of defined radio stations: %s" % config.get_station_ids()
    )
    parser.add_argument('-d', metavar='destination', required=False, help='Destination directory')

    detailled_group = parser.add_mutually_exclusive_group()
    detailled_group.add_argument('-l', metavar='length', required=False, help='Length of recording in seconds')
    detailled_group.add_argument('-s', metavar='station', required=False, help='Name of the station, defined in ~/.capturadio/capturadiorc.')
    detailled_group.add_argument('-b', metavar='broadcast', required=False, help='Title of the broadcast')
    detailled_group.add_argument('-t', metavar='title', required=False, help='Title of the recording')

    show_group = parser.add_mutually_exclusive_group()
    show_group.add_argument('-S', metavar='show', required=False, help='ID of the show, has to  be defined in configuration file')

    args = parser.parse_args()

    if args.S is not None:
        show_ids = map(lambda id: id.encode('ascii'), config.shows.keys())
        if args.S not in config.shows.keys():
            print "Show '%s' is unknown. Use one of these: %s." % (args.S, show_ids)
            exit(1)
        else:
          show = config.shows[args.S]
    else:
        duration = parse_duration(args.l)
        if (duration < 1):
            print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
            exit(1)

        if args.d is not None:
            config.set_destination(os.path.expanduser(args.d))

        if args.s not in config.get_station_ids():
            print "Station '%s' is unknown. Use one of these: %s." % (args.s, config.get_station_ids())
            exit(1)
        else:
            station = config.stations[str.lower(args.s)]

        title = u'%s' % unicode(args.t if (args.t is not None) else args.b, 'utf8')
        show = config.add_show(station, title, title, duration)

    recorder = Recorder(config)
    recorder.capture(show)
