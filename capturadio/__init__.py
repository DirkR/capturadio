__author__ = 'dirk'
try:
    # For Python 3.0 and later
    from urllib.request import urlopen, HTTPError, URLError, Request
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, HTTPError, URLError, Request
import time
import os
import logging
import re
import tempfile
try:
    # Python 2.x
    from mutagen.id3 import ID3, TIT2, TDRC, TCON, TALB, TLEN, TPE1, TCOP, COMM, TCOM, APIC
except ImportError:
    # Python 3.x
    from mutagenx.id3 import ID3, TIT2, TDRC, TCON, TALB, TLEN, TPE1, TCOP, COMM, TCOM, APIC
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser
from capturadio.util import format_date, slugify, parse_duration

version = (0, 9, 0)
version_string = ".".join(map(str, version))


class Configuration:   # implements Borg pattern
    configuration_folder = os.path.expanduser('~/.capturadio')
    filename = 'capturadiorc'

    _shared_state = {}

    def __init__(self, **kwargs):
        if 'reset' in kwargs and kwargs['reset']:
            Configuration._shared_state = {}
            del kwargs['reset']
            self.__dict__ = Configuration._shared_state
            if len(self.__dict__) == 0:
                if 'folder' in kwargs:
                    self.folder = kwargs['folder']
                else:
                    self.folder = Configuration.configuration_folder
                    if not os.path.exists(self.folder):
                        raise IOError("Configuration folder '%s' doesn't exist." % unicode(self.folder))

        if 'filename' in kwargs:
            self.filename = os.path.join(self.folder, kwargs['filename'])
        else:
            self.filename = os.path.join(self.folder, Configuration.filename)

        logging.basicConfig(
            filename=os.path.join(self.folder, 'log'),
            format='[%(asctime)s] %(levelname)-6s %(module)s::%(funcName)s:%(lineno)d: %(message)s',
            level=logging.DEBUG,
        )

        self.stations = {}
        self.shows = {}
        self.default_logo_url = None
        if 'destination' in kwargs:
            self.destination = kwargs['destination']
        else:
            self.destination = os.getcwd()
            self.tempdir = tempfile.gettempdir()
            self.date_pattern = "%Y-%m-%d %H:%M"
            self.comment_pattern = '''Show: %(show)s
Date: %(date)s
Website: %(link_url)s
Copyright: %(year)s %(station)s'''
        self.log = logging.getLogger('capturadio.config')
        self.feed = {}
        self._load_config()

    def _load_config(self):
        config_file = os.path.expanduser(self.filename)
        self.log.debug("Enter _load_config(%s)" % config_file)

        config = ConfigParser()
        config.changed_settings = False  # track changes

        config.read(config_file)
        if config.has_section('settings'):
            self.set_destination(config.get('settings', 'destination', os.getcwd()))
            if config.has_option('settings', 'date_pattern'):
                self.date_pattern = config.get('settings', 'date_pattern')
            if config.has_option('settings', 'tempdir'):
                self.tempdir = os.path.abspath(os.path.expanduser(config.get('settings', 'tempdir')))
                if not os.path.exists(self.tempdir):
                    os.makedirs(self.tempdir)
            if config.has_option('settings', 'comment_pattern'):
                pattern = config.get('settings', 'comment_pattern')
                pattern = re.sub(r'%([a-z_][a-z_]+)', r'%(\1)s', pattern)
                self.comment_pattern = pattern
        self._read_feed_settings(config)
        self._add_stations(config)
        if config.changed_settings:
            new_file = open(config_file + '.new', 'w')
            config.write(new_file)
            new_file.close()
            print("WARNING: Saved a updated version of config file as '%s.new'." % (config_file))

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
            if config.has_option('feed', 'default_link_url'):
                self.default_link_url = config.get('feed', 'default_link_url')
            else:
                self.feed['default_link_url'] = 'http://www.podcast.de/'

                # Read stations


    def _add_stations(self, config):
        self.log.debug("Enter _add_stations")
        if config.has_section('stations'):
            for station_id in config.options('stations'):
                station_stream = config.get('stations', station_id)
                station_name = station_id
                station_logo_url = self.default_logo_url
                if config.has_section(station_id):
                    if config.has_option(station_id, 'name'):
                        station_name = u'%s' % unicode(config.get(station_id, 'name'), 'utf8')
                    if config.has_option(station_id, 'logo_url'):
                        station_logo_url = config.get(station_id, 'logo_url')
                station = self.add_station(station_id, station_stream, station_name, station_logo_url)
                if config.has_option(station_id, 'shows'):
                    show_ids = re.split(r',? +', config.get(station_id, 'shows'))
                    for show_id in show_ids:
                        if config.has_section(show_id):
                            config.set(show_id, 'station', station_id)
                            print("WARNING: removed legacy setting 'shows' for show '%s' of station '%s' in configuration file." % (
                                show_id, station_id))
                        else:
                            config.add_section(show_id)
                            config.set(show_id, 'station', station_id)
                            print("WARNING: added show section '%s' in configuration file." % (show_id))
                    config.remove_option(station_id, 'shows')
                    config.changed_settings = True

                if config.has_option(station_id, 'link_url'):
                    station.link_url = config.get(station_id, 'link_url')
                else:
                    station.link_url = self.feed['base_url']

                if config.has_option(station_id, 'date_pattern'):
                    station.date_pattern = config.get(station_id, 'date_pattern')

                self._add_shows(config, station)


    def _add_shows(self, config, station):

        for section_name in config.sections():
            if config.has_option(section_name, 'station') and config.get(section_name, 'station') == station.id:
                show_id = section_name
                if config.has_option(show_id, 'title'):
                    show_title = u'%s' % unicode(config.get(show_id, 'title'), 'utf8')
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

                if config.has_option(show_id, 'date_pattern'):
                    show.date_pattern = config.get(show_id, 'date_pattern')


    def set_destination(self, destination):
        if destination is not None:
            destination = os.path.expanduser(destination)
            if not os.path.isdir(destination):
                os.makedirs(destination)
            destination = os.path.realpath(os.path.abspath(os.path.expanduser(destination)))
            self.destination = unicode(destination)
            return self.destination
        #raise Exception("Could not set destination %s" % destination)

    def __repr__(self):
        return pformat(list(self))

    def get_station_ids(self):
        if self.stations is not None:
            return self.stations.keys()
        else:
            return None

    def add_station(self, id, stream_url, name=None, logo_url=None):
        station = Station(unicode(id, 'utf-8'), stream_url, name, logo_url)
        self.stations[id] = station
        self.log.debug(u'  %s' % station)
        return station

    def add_show(self, station, id, name, duration, logo_url=None):
        if not isinstance(station, Station):
            raise TypeError('station has to be of type "Station"')
        show = Show(station, id, name, duration, logo_url)
        self.log.debug(u'    %s' % show)
        self.shows[id] = show
        return show


class Station:
    """Describes a radio station, consists of shows."""

    def __init__(self, id, stream_url, name, logo_url=None):
        self.id = id
        self.name = name
        self.stream_url = stream_url
        self.logo_url = logo_url
        self.shows = []
        self.registry = None

    def __repr__(self):
        return 'Station(id=%s, name=%s, show_count=%d)' % (self.id, unicode(self.name), len(self.shows))

    def __str__(self):
        return 'Station(id=%s, name=%s, show_count=%d)' % (self.id, unicode(self.name), len(self.shows))

    def get_link_url(self):
        if 'link_url' in self.__dict__:
            return self.link_url

    def get_date_pattern(self):
        if 'date_pattern' in self.__dict__:
            return self.date_pattern
        else:
            config = Configuration()
            return config.date_pattern


class Show:
    """Describes a single show, consists of episodes and belongs to a station"""

    def __init__(self, station, id, name, duration, logo_url=None):
        if not isinstance(station, Station):
            raise TypeError('station has to be of type "Station"')

        self.station = station
        self.id = id
        self.name = name
        self.duration = duration
        self.logo_url = logo_url
        station.shows.append(self)

    def __repr__(self):
        return 'Show(id=%s, name=%s, duration=%d, station_id=%s)' % (
            self.id, unicode(self.name), self.duration, self.station.id)

    def __str__(self):
        return 'Show(id=%s, name=%s, duration=%d, station_id=%s)' % (
            self.id, unicode(self.name), self.duration, self.station.id)

    def get_link_url(self):
        if 'link_url' in self.__dict__:
            return self.link_url
        else:
            return self.station.get_link_url()

    def get_date_pattern(self):
        if 'date_pattern' in self.__dict__:
            return self.date_pattern
        else:
            return self.station.get_date_pattern()

    def get_stream_url(self):
        return self.station.stream_url


class Recorder:
    def __init__(self):
        self.log = logging.getLogger('capturadio.recorder')
        self.start_time = None

    def capture(self, show):
        config = Configuration()

        self.log.info(u'capture "%s" from "%s" for %s seconds to %s' %\
                      (show.name, show.station.name, show.duration, config.destination))

        self.start_time = time.time()
        file_name = u"%s/capturadio_%s.mp3" % (config.tempdir, os.getpid())
        try:
            self._write_stream_to_file(show.get_stream_url(), file_name, show.duration)

            time_string = format_date(config.date_pattern, time.localtime(self.start_time))
            target_file = u"%(station)s/%(show)s/%(show)s_%(time)s.mp3" %\
                   { 'station' : show.station.name,
                     'show': show.name,
                     'time': time_string,
                   }
            target_file = os.path.join(config.destination, slugify(target_file))
            final_file_name = self._copy_file_to_destination(file_name, target_file)
            self._add_metadata(show, final_file_name)
            self.start_time = None
        except Exception as e:
            message = "Could not complete capturing, because an exception occured: %s" % e
            self.log.error(message)
            raise e
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

    def _write_stream_to_file(self, stream_url, file_name, duration):
        not_ready = True
        self.log.info("write %s to %s" % (stream_url, file_name))
        try:
            file = open(file_name, 'w+b')
            stream = urlopen(stream_url)
            while not_ready:
                file.write(stream.read(10240))
                if time.time() - self.start_time > duration:
                    not_ready = False
            file.close()
        except Exception as e:
            message = "Could not capture show, because an exception occured: %s" % e.message
            self.log.error("_write_stream_to_file: %s" % message)
            os.remove(file_name)
            raise e

    def _copy_file_to_destination(self, file_name, target_file):
        import shutil

        if not os.path.isdir(os.path.dirname(target_file)):
            os.makedirs(os.path.dirname(target_file))
        try:
            shutil.copyfile(file_name, target_file)
            self.log.info(u"file copied from %s to %s" % (file_name, target_file))
            return target_file
        except IOError as e:
            message = "Could not copy tmp file to %s: %s" % (target_file, e.message)
            self.log.error("_copy_file_to_destination: %s" % message)
            os.remove(file_name)
            raise IOError(message, e)

    def _add_metadata(self, show, file_name):
        if file_name is None:
            raise "file_name is not set - you cannot add metadata to None"

        config = Configuration()

        time_string = format_date(config.date_pattern, time.localtime(self.start_time))
        comment = config.comment_pattern % {
            'show': show.name,
            'date': time_string,
            'year': time.strftime('%Y', time.gmtime()),
            'station': show.station.name,
            'link_url': show.get_link_url()
        }

        audio = ID3()
        # See http://www.id3.org/id3v2.3.0 for details about the ID3 tags

        audio.add(TIT2(encoding=2, text=["%s, %s" % (show.name, time_string)]))
        audio.add(TDRC(encoding=2, text=[format_date('%Y-%m-%d %H:%M', self.start_time)]))
        audio.add(TCON(encoding=2, text=[u'Podcast']))
        audio.add(TALB(encoding=2, text=[show.name]))
        audio.add(TLEN(encoding=2, text=[show.duration * 1000]))
        audio.add(TPE1(encoding=2, text=[show.station.name]))
        audio.add(TCOP(encoding=2, text=[show.station.name]))
        audio.add(COMM(encoding=2, lang='eng', desc='desc', text=comment))
        audio.add(TCOM(encoding=2, text=[show.get_link_url()]))
        self._add_logo(show, audio)
        audio.save(file_name)

    def _add_logo(self, show, audio):
        # APIC part taken from http://mamu.backmeister.name/praxis-tipps/pythonmutagen-audiodateien-mit-bildern-versehen/
        url = show.station.logo_url
        if url is not None:
            request = Request(url)
            request.get_method = lambda: 'HEAD'
            try:
                response = urlopen(request)
                logo_type = response.info().gettype()

                if logo_type in ['image/jpeg', 'image/png']:
                    img_data = urlopen(url).read()
                    img = APIC(
                        encoding=3,  # 3 is for utf-8
                        mime=logo_type,
                        type=3,  # 3 is for the cover image
                        desc=u'Station logo',
                        data=img_data
                    )
                    audio.add(img)
            except (HTTPError, URLError) as e:
                message = "Error during capturing %s - %s" % (url, e)
                self.log.error(message)
            except Exception as e:
                raise e
