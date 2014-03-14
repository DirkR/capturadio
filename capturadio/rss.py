import datetime as dt
import urllib
import os
import time
import logging
import PyRSS2Gen
try:
    # Python 2.x
    from mutagen.mp3 import MP3, HeaderNotFoundError
except ImportError:
    # Python 3.x
    from mutagenx.mp3 import MP3, HeaderNotFoundError
from capturadio import Configuration
from capturadio import version_string as capturadio_version
from capturadio.util import url_fix, format_date


class Audiofile:
    def __init__(self, filename):
        self.log = logging.getLogger('create_podcast_feed.Audiofile')
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
            self.log.error("Couldn't find MPEG header in file %r" % self.path)
        self.size = os.path.getsize(self.path)
        self.pubdate = dt.datetime.fromtimestamp(os.path.getmtime(self.path))

    def extract_metadata(self, audio):

        self.title = self.get_mp3_tag(audio, 'TIT2', self.basename[:-4])
        self.show = self.get_mp3_tag(audio, 'TALB', None)
        if self.show is None:
            self.show = self.basename[:-4]
        else:
            for s in self.config.shows.values():
                if unicode(s.name) == self.show:
                    self.link = s.get_link_url()
                    break
        default_date = format_date(self.config.date_pattern, time.time())
        self.date = self.get_mp3_tag(audio, 'TDRC', default_date)
        self.artist = self.get_mp3_tag(audio, 'TPE1', self.show)
        __playtime = self.get_mp3_tag(audio, 'TLEN', None)
        if __playtime is not None:
            self.playtime = int(__playtime) / 1000
        else:
            self.playtime = 0
        self.copyright = self.get_mp3_tag(audio, 'TCOP', self.artist)
        __description = u'Show: %s<br>Episode: %s<br>Copyright: %s %s' % (
            self.show, self.title, self.date[:4], self.copyright)
        self.description = self.get_mp3_tag(audio, "COMM:desc:'eng'", __description)
        self.link = self.get_mp3_tag(audio, "TCOM", u'http://www.podcast.de/')

    def get_mp3_tag(self, audio, tag_string, default):
        try:
            return u"%s" % audio[tag_string]
        except KeyError:
            default


class Audiofiles:
    """
    A collection of audiofiles and some metadata, used as the basis for at
    """

    files_cache = {}

    def __init__(self, local_path=''):
        self.log = logging.getLogger('create_podcast_feed.Audiofiles')
        self.log.info('Create Audiofiles(%s)' % local_path)
        self.config = Configuration()

        feed_title = self.config.feed['title']
        if (local_path != ''):
            feed_title += " - " + local_path.replace('/', ' - ')

        self.path = local_path
        self.title = feed_title
        self.link = self.config.feed['about_url']
        self.description = self.config.feed['description']
        self.language = self.config.feed['language']

        self.urlbase = self.config.feed['base_url']
        if local_path is not '':
            self.urlbase += urllib.quote(local_path)

        if not self.urlbase.endswith('/'):
            self.urlbase += '/'

        self.data = []

        self.generator = 'CaptuRadio v%s' % capturadio_version

    def readfolder(self, dirname):
        self.log.info(u'readfolder: processing %s' % dirname)

        self.dirname = dirname
        for dirname, dirnames, filenames in os.walk(dirname):
            for filename in filenames:
                path = os.path.join(dirname, filename)
                if os.path.exists(path) and \
                    os.path.isfile(path) and \
                        path.endswith(".mp3"):
                    self.data.append(self._get_audiofile(path))

    def _get_audiofile(self, path):
        self.log.info(u'Enter _get_audiofile(%s)' % path)
        if path not in Audiofiles.files_cache.keys():
            audio_file = Audiofile(path)
            Audiofiles.files_cache[path] = audio_file
        else:
            audio_file = Audiofiles.files_cache[path]
        return audio_file

    def rssitems(self, n=10):
        result = []
        for file in self.data:
            rssitem = ItunesRSSItem(
                title=file.title,
                link=file.link if 'link' in file.__dict__ else 'http://www.podcast.de/',
                author=file.artist,
                description=file.description,
                pubDate=file.pubdate,
                guid=PyRSS2Gen.Guid(file.url),
                enclosure=PyRSS2Gen.Enclosure(
                    file.url,
                    file.filesize,
                    "audio/mpeg"
                )
            )
            rssitem.image = self._create_image_tag(rssitem)
            rssitem.duration = str(dt.timedelta(seconds=file.playtime))
            result.append(rssitem)

        waste = [(i.pubDate, i) for i in result]
        waste.sort()
        waste.reverse()
        waste = waste[:n]
        result = [pair[1] for pair in waste]

        self.log.debug(u'  rssitems: Found %d items' % len(result))
        return result

    def getrss(self, n=10):
        items = self.rssitems(n)
        config = Configuration()

        image = PyRSS2Gen.Image(
            url=config.default_logo_url,
            title=config.feed['title'],
            link=config.feed['about_url'],
            description=u"%s\n\nLogo: %s" % (
                config.feed['description'],
                config.feed['logo_copyright']
            )
        )

        channel = ItunesRSS(
            title=self.title,
            link=self.link,
            description=self.description,
            language=self.language,
            generator=self.generator,
            lastBuildDate=dt.datetime.now(),
            items=items,
            image=image
        )

        return channel

    def _create_image_tag(self, rssitem):
        logo_url = self._get_logo_url(rssitem.author)
        link_url = self._get_link_url(rssitem.author)
        config = Configuration()

        if logo_url is not None:
            return PyRSS2Gen.Image(
                url=logo_url,
                title=rssitem.author,
                link=link_url
            )
        else:
            return PyRSS2Gen.Image(
                url=config.default_logo_url,
                title=rssitem.author, link=link_url
            )

    def _get_link_url(self, station_name):
        for id, station in self.config.stations.items():
            if station_name == station.name:
                self.log.debug(u'    %s: found %s' % (
                    station_name,
                    station.link_url,
                ))
                return station.link_url
        self.log.debug(u'    %s: found noting' % station_name)
        return None

    def _get_logo_url(self, station_name):
        for id, station in self.config.stations.items():
            if station_name == station.name:
                self.log.debug(u'    %s: found %s' % (
                    station_name,
                    station.logo_url,
                ))
                return station.logo_url
        self.log.debug(u'    %s: found noting' % station_name)
        return None


class ItunesRSS(PyRSS2Gen.RSS2):
    """This class adds the "itunes" extension (<itunes:image>, etc.)
    to the rss feed."""

    rss_attrs = {
        "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        "version": "2.0",
    }

    def publish_extensions(self, handler):
        # implement this method to embed the <itunes:*> elements
        # into the channel header.
        if self.image is not None and \
            isinstance(self.image, PyRSS2Gen.Image) and \
                self.image.url is not None:
            handler.startElement('itunes:image',  {'href': self.image.url})
            handler.endElement('itunes:image')


class ItunesRSSItem(PyRSS2Gen.RSSItem):
    """This class adds the "itunes" extension (<itunes:image>, etc.)
    to the rss feed item."""

    def publish_extensions(self, handler):
        # implement this method to embed the <itunes:*> elements
        # into the channel header.
        if self.duration is not None:
            PyRSS2Gen._opt_element(handler, "itunes:duration", self.duration)
        if self.image is not None and \
            isinstance(self.image, PyRSS2Gen.Image) and \
                self.image.url is not None:
            handler.startElement('itunes:image',  {'href': self.image.url})
            handler.endElement('itunes:image')
