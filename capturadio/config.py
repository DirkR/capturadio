import codecs
import logging
import os
import re
import tempfile
from configparser import ConfigParser, DEFAULTSECT

from capturadio import Station, Show
from capturadio.util import parse_duration


class UnicodeConfigParser(ConfigParser):
    """The class UnicodeConfigParser is derived from RawConfigParser and
    overloads the method write() to output unicode data."""

    def __init__(self, *args, **kwargs):
        ConfigParser.__init__(self, *args, **kwargs)

    def write(self, fp):
        """Fixed for Unicode output"""
        text = str
        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
            for (key, value) in self._defaults.items():
                fp.write("%s = %s\n" % (key, text(value).replace('\n', '\n\t')))
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for (key, value) in self._sections[section].items():
                if key != "__name__":
                    fp.write("%s = %s\n" %
                                (key, text(value).replace('\n','\n\t')))
            fp.write("\n")


class Configuration(object):   # implements Borg pattern
    folder = os.getcwd()
    filename = 'capturadiorc'

    _shared_state = {}
    _loaded_from_disk = False

    @staticmethod
    def _reset():
        import socket
        hostname = socket.gethostname()
        if hostname.endswith('uberspace.de'):
            hostname = '%s.%s' % (os.environ["USER"], hostname)
            destination = '~/html/podcasts'
        elif os.uname()[0] == 'Darwin':
            destination = '~/Sites/podcasts'
        else:
            destination = '~/public_html/podcasts'

        Configuration._shared_state = {
            'folder': Configuration.folder,
            'filename': os.path.join(
                Configuration.folder,
                Configuration.filename
            ),
            'destination': destination,
            'stations': {},
            'shows': {},
            'tempdir': tempfile.gettempdir(),
            'date_pattern': r"%Y-%m-%d",
            'comment_pattern': '''Show: %(show)s
Date: %(date)s
Website: %(link_url)s
Copyright: %(year)s %(station)s''',
            'feed': {
                'title': 'Internet Radio Recordings',
                'base_url': 'http://%s/podcasts' % hostname,
                'about_url': 'http://%s/podcasts/about.html' % hostname,
                'default_link_url': 'http://www.podcast.de/',
                'default_logo_url': 'http://www.podcast.de/default.png',
                'logo_copyright': None,
                'description': 'My Radio Recordings',
                'language': 'en',
                'filename': 'rss.xml',
            },
        }
        Configuration._loaded_from_disk = False

    def __init__(self, **kwargs):
        if 'reset' in kwargs and kwargs['reset']:
            Configuration._reset()
            del kwargs['reset']
        if len(Configuration._shared_state) == 0:
            Configuration._reset()

        self.__dict__ = Configuration._shared_state

        if 'folder' in kwargs:
            self.folder = kwargs['folder']
            self.filename = os.path.join(
                self.folder,
                kwargs['filename'] if 'filename' in kwargs else Configuration.filename
            )
            if not os.path.exists(self.folder):
                os.makedirs(self.folder)

        if 'destination' in kwargs:
            self.destination = kwargs['destination']

        if not os.path.exists(self.filename):
            self.write_config()
        else:
            if not Configuration._loaded_from_disk:
                self._load_config()
                Configuration._loaded_from_disk = True

    def write_config(self):
        logging.debug('Enter write_config')
        config = UnicodeConfigParser()
        config.add_section('settings')
        for key in ('destination', 'date_pattern', 'comment_pattern'):
            if self.__dict__[key] is not None:
                config.set('settings', key, self.__dict__[key])

        config.add_section('feed')
        for key in ('base_url', 'title', 'about_url', 'description',
                    'language', 'filename', 'default_logo_url',
                    'default_link_url'):
            if self.feed[key] is not None:
                config.set('feed', key, self.feed[key])
        if self.feed['logo_copyright'] is not None:
            config.set(
                'feed',
                'default_logo_copyright',
                self.feed['logo_copyright']
            )

        config.add_section('stations')
        for station in self.stations.values():
            config.set('stations', station.id, station.stream_url)
            config.add_section(station.id)
            for key, value in station.__dict__.items():
                if key in ('id', 'shows'):
                    continue
                if value is not None:
                    config.set(station.id, key, value)

        for show in self.shows.values():
            config.add_section(show.id)
            for key, value in show.__dict__.items():
                if key in ('id'):
                    continue
                if value is not None:
                    if isinstance(value, Station):
                        config.set(show.id, key, value.id)
                    else:
                        config.set(show.id, key, value)

        folder = os.path.dirname(self.filename)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(self.filename, 'w') as file:
            config.write(file)


    def _load_config(self):
        config_file = os.path.expanduser(self.filename)
        logging.debug("Enter _load_config(%s)" % config_file)

        config = UnicodeConfigParser()
        Configuration.changed_settings = False  # track changes

        config.readfp(codecs.open(config_file, "r", "utf8"))
        if config.has_section('settings'):
            if config.has_option('settings', 'destination'):
                self.set_destination(config.get('settings', 'destination'))
            if config.has_option('settings', 'date_pattern'):
                self.date_pattern = config.get('settings', 'date_pattern', raw=True)
            if config.has_option('settings', 'tempdir'):
                self.tempdir = os.path.abspath(os.path.expanduser(config.get('settings', 'tempdir')))
                if not os.path.exists(self.tempdir):
                    os.makedirs(self.tempdir)
            if config.has_option('settings', 'comment_pattern'):
                pattern = config.get('settings', 'comment_pattern', raw=True)
                pattern = re.sub(r'%([a-z_][a-z_]+)', r'%(\1)s', pattern)
                self.comment_pattern = pattern
        self._read_feed_settings(config)
        self._add_stations(config)
        if Configuration.changed_settings:
            import shutil
            shutil.copy(config_file, config_file + '.bak')
            with codecs.open(config_file, 'w', 'utf8') as file:
                config.write(file)
            print("WARNING: Saved the old version of config file as '%s.bak' and updated configuration." % (config_file))


    def _read_feed_settings(self, config):
        if config.has_section('feed'):
            if config.has_option('feed', 'default_logo_url'):
                self.default_logo_url = config.get('feed', 'default_logo_url')
            if config.has_option('feed', 'base_url'):
                self.feed['base_url'] = config.get('feed', 'base_url')
            if config.has_option('feed', 'url'):
                if not config.has_option('feed', 'base_url'):
                    self.feed['base_url'] = config.get('feed', 'url')
                    config.set('feed', 'base_url', self.feed['base_url'])
                    print("WARNING: Replaced setting 'feed.url' with 'feed.base_url' in configuration file.")
                else:
                    print("WARNING: Removed setting 'feed.url' from configuration file.")
                config.remove_option('feed', 'url')
                Configuration.changed_settings = True
            if config.has_option('feed', 'title'):
                self.feed['title'] = config.get('feed', 'title')
            if config.has_option('feed', 'about_url'):
                self.feed['about_url'] = config.get('feed', 'about_url')
            if config.has_option('feed', 'description'):
                self.feed['description'] = config.get('feed', 'description')
            if config.has_option('feed', 'language'):
                self.feed['language'] = config.get('feed', 'language')
            if config.has_option('feed', 'filename'):
                self.feed['filename'] = config.get('feed', 'filename')
            if config.has_option('feed', 'default_logo_copyright'):
                self.feed['logo_copyright'] = config.get('feed', 'default_logo_copyright')
            if config.has_option('feed', 'default_logo_url'):
                self.feed['default_logo_url'] = config.get('feed', 'default_logo_url')
            if config.has_option('feed', 'default_link_url'):
                self.feed['default_link_url'] = config.get('feed', 'default_link_url')

            if self.feed['base_url'].endswith('/'):
                self.feed['base_url'] = self.feed['base_url'][:-1]
            # Read stations


    def _add_stations(self, config):
        logging.debug("Enter _add_stations")
        if config.has_section('stations'):
            for station_id in config.options('stations'):
                station_stream = config.get('stations', station_id)
                station_name = station_id
                if config.has_section(station_id):
                    if config.has_option(station_id, 'name'):
                        station_name = config.get(station_id, 'name')
                station = self.add_station(station_id, station_stream, station_name)
                if config.has_option(station_id, 'shows'):
                    show_ids = re.split(r',? +', config.get(station_id, 'shows'))
                    for show_id in show_ids:
                        if config.has_section(show_id):
                            config.set(show_id, 'station', station_id)
                            logging.warning("Removed legacy setting 'shows' for show '%s' of station '%s' in configuration file." % (
                                show_id, station_id))
                        else:
                            config.add_section(show_id)
                            config.set(show_id, 'station', station_id)
                            logging.warning("Added show section '%s' in configuration file." % (show_id))
                    config.remove_option(station_id, 'shows')
                    Configuration.changed_settings = True

                if config.has_option(station_id, 'logo_url'):
                    station.logo_url = config.get(station_id, 'logo_url')

                if config.has_option(station_id, 'link_url'):
                    station.link_url = config.get(station_id, 'link_url')

                if config.has_option(station_id, 'date_pattern'):
                    station.date_pattern = config.get(station_id, 'date_pattern', raw=True)

                self._add_shows(config, station)


    def _add_shows(self, config, station):

        for section_name in config.sections():
            if config.has_option(section_name, 'station') and config.get(section_name, 'station') == station.id:
                show_id = section_name
                if config.has_option(show_id, 'title'):
                    show_title = config.get(show_id, 'title')
                    logging.warning("Setting 'title' of show '%s' is deprecated and should be replaced by 'name'." % show_id)
                elif config.has_option(show_id, 'name'):
                    show_title = config.get(show_id, 'name')
                else:
                    raise Exception('No "title" or "name" option defined for show "%s".' % show_id)

                if config.has_option(show_id, 'duration'):
                    show_duration = parse_duration(config.get(show_id, 'duration'))
                else:
                    raise Exception('No duration option defined for show "%s".' % show_id)

                show = self.add_show(self, station, show_id, show_title, show_duration)

                if config.has_option(show_id, 'logo_url'):
                    show.logo_url = config.get(show_id, 'logo_url')

                if config.has_option(show_id, 'link_url'):
                    show.link_url = config.get(show_id, 'link_url')

                if config.has_option(show_id, 'stream_url'):
                    show.stream_url = config.get(show_id, 'stream_url')

                if config.has_option(show_id, 'date_pattern'):
                    show.date_pattern = config.get(show_id, 'date_pattern', raw=True)


    def set_destination(self, destination):
        if destination is not None:
            destination = os.path.expanduser(destination)
            if not os.path.isdir(destination):
                os.makedirs(destination)
            self.destination = os.path.realpath(os.path.abspath(os.path.expanduser(destination)))
            return self.destination
        #raise Exception("Could not set destination %s" % destination)


    def get_station_ids(self):
        if self.stations is not None:
            return list(self.stations.keys())
        else:
            return None


    def add_station(self, id, stream_url, name=None):
        station = Station(self, id, stream_url, name)
        self.stations[id] = station
        logging.debug(u'  %s' % station)
        return station


    def add_show(self, config, station, id, name, duration):
        if not isinstance(station, Station):
            raise TypeError('station has to be of type "Station"')
        show = Show(config, station, id, name, duration)
        logging.debug(u'    %s' % show)
        self.shows[id] = show
        return show