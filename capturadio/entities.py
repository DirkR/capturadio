import datetime
import os
import time

from capturadio.util import slugify


class Entity(object):

    def __init__(self, id, name=None):
        self.id = id
        self.name = name
        self.logo_url = None
        self.link_url = None
        self.slug = None
        self.language = "en"


    def __str__(self):
        return '{}("{}")'.format(self.__class__.__qualname__, self.name)


def __repr__(self):
    return '{}(id="{}", name="{}", slug="{}", language="{}")'.format(
        self.__class__.__qualname__, self.id, self.name, self.slug, self.language)


class Station(Entity):
    """Describes a radio station, consists of shows."""

    def __init__(self, config, id, stream_url, name):
        super(Station, self).__init__(id, name)
        self.stream_url = stream_url
        self.logo_url = config.feed['default_logo_url']
        self.link_url = config.feed['base_url']
        self.language = config.feed['language']
        self.shows = []
        self.date_pattern = config.date_pattern
        self.slug = slugify(self.id)
        self.filename = os.path.join(config.destination, self.slug)


    def __repr__(self):
        return '{}(id={}, name={}, show_count={:d})'.format(self.__class__.__qualname__, self.id, self.name, len(self.shows))


class Show(Entity):
    """
    Describes a single show, consists of episodes and belongs to a station.
    """

    def __init__(self, config, station, id, name, duration):
        if not isinstance(station, Station):
            raise TypeError('station has to be of type "Station"')
        super(Show, self).__init__(id, name)
        self.station = station
        self.stream_url = station.stream_url
        self.link_url = station.link_url
        self.logo_url = station.logo_url
        self.language = station.language
        self.date_pattern = station.date_pattern
        self.author = station.name
        self.duration = duration
        self.slug = os.path.join(station.slug, slugify(self.id))
        self.filename = os.path.join(config.destination, self.slug)
        station.shows.append(self)

    def __repr__(self):
        return 'Show(id=%s, name=%s, duration=%d, station_id=%s)' % (
            self.id, self.name, self.duration, self.station.id)


class Episode(Entity):
    """
    Describes an episode of a show.
    """

    def __init__(self, config, show):
        if not isinstance(show, Show):
            raise TypeError('show has to be of type "Show"')

        super(Episode, self).__init__(show.id)
        self.__dict__ = show.__dict__.copy()

        self.starttime = time.localtime()
        self.show = show
        self.name = "{}, {}".format(show.name, time.strftime(config.date_pattern, self.starttime))
        self.pubdate = time.strftime('%c', self.starttime)
        self.slug = os.path.join(
            show.slug,
            "{}_{}.mp3".format(
                slugify(self.show.id),
                time.strftime('%Y-%m-%d_%H-%M', self.starttime)
            )
        )
        self.filename = os.path.join(config.destination, self.slug)
        self.duration_string = str(datetime.timedelta(seconds=self.duration))

    def __repr__(self):
        print(self.__class__.__dict__)
        return '{}(id={}, name={}, pubdate={}, show_id={})'\
            .format(self.__class__, self.id, self.name, self.pubdate, self.show.id)

    def __lt__(self, other):
        return self.starttime < other.starttime