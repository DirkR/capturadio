#!/usr/bin/env python2.7
# This script traverses a directory tree and creates a rss file in the root folder
# containing all found mp3 files as items
# Original found at
# Found at http://snippsnapp.polite.se/wiki?action=browse&diff=0&id=PyPodcastGen
# and adopted for my needs

import datetime, urllib, string, os, time, logging
import PyRSS2Gen
from mutagen.mp3 import MP3, HeaderNotFoundError
from mutagen.easyid3 import EasyID3
import re
from capturadio import Configuration
from capturadio import version_string as capturadio_version
from capturadio.rss import ItunesRSS, ItunesRSSItem
from capturadio.util import format_date, url_fix

class Audiofile:
    def __init__(self, filename):
        self.log = logging.getLogger('create_podcast_feed.Audiofile')

        config = Configuration()

        self.path = filename
        self.basename = os.path.basename(filename)
        local_path = self.path.replace(config.destination, '')
        self.url = config.feed['base_url'] + url_fix(local_path)

        try:
          audio = MP3(self.path)
        except HeaderNotFoundError, e:
          self.log.error('Could not find MPEG header in file "%s"' % self.path)


        try:
            self.title = u"%s" % audio['TIT2']
        except KeyError, e:
            self.title = self.basename[:-4]

        try:
            self.show = u"%s" % audio['TALB']

            for s in config.shows.values():
                if unicode(s.name) == self.show:
                    self.link = s.get_link_url()


        except KeyError, e:
            self.show = self.basename[:-4]

        try:
            self.date = u"%s" % audio['TDRC']
        except KeyError, e:
            self.date = format_date(config.date_pattern, time.time())

        try:
            self.artist = u"%s" % audio['TPE1']
        except KeyError, e:
            self.artist = self.show

        try:
            self.playtime = audio.info.length
        except:
            self.playtime = 0

        try:
            self.copyright = u"%s" % audio['TCOP']
        except KeyError, e:
            self.copyright = self.artist

        try:
            self.description = u"%s" % audio["COMM:desc:'eng'"]
        except:
            self.description = u'Show: %s<br>Episode: %s<br>Copyright: %s %s' % (
                    self.show, self.title, self.date[:4], self.copyright)

        try:
            self.link = u"%s" % audio['TCOM']
        except:
            self.link = u'http://www.podcast.de/'

        self.size = os.path.getsize(self.path)
        self.pubdate = datetime.datetime.fromtimestamp(os.path.getmtime(self.path))


class Audiofiles:
    """
    A collection of audiofiles and some metadata, used as the basis for at 
    
    """

    files_cache = {}

    def __init__(self, local_path=''):
        self.log = logging.getLogger('create_podcast_feed.Audiofiles')
        self.log.info('Create Audiofiles(%s)' % local_path)

        config = Configuration()

        feed_title = config.feed['title']
        if (local_path != ''):
            feed_title += " - " + string.replace(local_path, '/', ' - ')

        self.path = local_path
        self.title = feed_title
        self.link = config.feed['about_url']
        self.description = config.feed['description']
        self.language = config.feed['language']

        self.urlbase = config.feed['base_url']
        if local_path is not '':
            self.urlbase += urllib.quote(local_path)

        if not self.urlbase.endswith('/'):
            self.urlbase += '/'

        self.data = []

        self.generator = 'CaptuRadio v%s' % capturadio_version

    def readfolder(self, dirname):
        self.log.info(u'readfolder: processing %s' % dirname)

        config = Configuration()

        self.dirname = dirname
        for dirname, dirnames, filenames in os.walk(dirname):
            for filename in filenames:
                path = os.path.join(dirname, filename)
                if os.path.exists(path) and os.path.isfile(path) and path.endswith(".mp3"):
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
        for audio_file in self.data:
            rssitem = ItunesRSSItem(
                title=audio_file.title,
                link=audio_file.link if 'link' in audio_file.__dict__ else 'http://www.podcast.de/',
                author=audio_file.artist,
                description=audio_file.description,
                pubDate=audio_file.pubdate,
                guid=PyRSS2Gen.Guid(audio_file.url),
                enclosure=PyRSS2Gen.Enclosure(audio_file.url, audio_file.playtime, "audio/mpeg")
            )
            rssitem.image = self._create_image_tag(rssitem)
            rssitem.length = str(datetime.timedelta(seconds=audio_file.playtime))
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

        channel = ItunesRSS(title=self.title,
            link=self.link,
            description=self.description,
            language=self.language,
            generator=self.generator,
            lastBuildDate=datetime.datetime.now(),
            items=items,
            image=image
        )

        return channel

    def _create_image_tag(self, rssitem):
        logo_url = self._get_logo_url(rssitem.author)
        link_url = self._get_link_url(rssitem.author)
        config = Configuration()

        if logo_url is not None:
            return PyRSS2Gen.Image(url=logo_url, title=rssitem.author,
                link=link_url)
        else:
            return PyRSS2Gen.Image(url=config.default_logo_url,
                title=rssitem.author, link=link_url)

    def _get_link_url(self, station_name):
        for id, station in config.stations.items():
            if station_name == station.name:
                self.log.debug(u'    %s: found %s' % (station_name, station.link_url))
                return station.link_url
        self.log.debug(u'    %s: found noting' % station_name)
        return None

    def _get_logo_url(self, station_name):
        for id, station in config.stations.items():
            if station_name == station.name:
                self.log.debug(u'    %s: found %s' % (station_name, station.logo_url))
                return station.logo_url
        self.log.debug(u'    %s: found noting' % station_name)
        return None


def process_folder(path, root_path):
    log = logging.getLogger('create_podcast_feed')
    log.debug('exec process_folder(path=%s, root_path=%s)' % (path, root_path))

    local_path = string.replace(path, root_path, '')
    if (local_path != ''):
        if (local_path.startswith('/')):
            local_path = local_path[1:]
        if (not local_path.endswith('/')):
            local_path += '/'

    audio_files = Audiofiles(local_path)
    audio_files.readfolder(path)

    rss_file = config.feed['file_name']

    rss = audio_files.getrss(20)
    if len(rss.items) > 0:
        rss.write_xml(open(os.path.join(path, rss_file), "w"))


def excluded_folder(dirname, patterns=['.git', '.bzr', 'svn', '.hg']):
    for p in patterns:
        pattern = r'.*%s%s$|.*%s%s%s.*' % (os.sep, p, os.sep, p, os.sep)
        if re.match(pattern, dirname) is not None:
            return True
    return False

if __name__ == "__main__":
    import argparse


    parser = argparse.ArgumentParser(
        description='Generate a rss file containing all mp3 files in this directory and all sub directories.')
    parser.add_argument('-C', metavar='configfile', required=False, help='Configuration file')
    parser.add_argument('-r',
        action='store_true',
        help="Put an rss file into every subfolder, that contains all episodes in all of it's subfolders.")
    parser.add_argument('directory',
        nargs='?',
        help='The directory to be indexed. Use current directory if ommitted.')
    args = parser.parse_args()

    if args.C is not None:
        if not os.path.exists(os.path.expanduser(args.C)):
            raise IOError('Configuration file "%s" does not exist' % args.C)
        Configuration.configuration_folder = os.path.dirname(os.path.expanduser(args.C))
        Configuration.filename = os.path.basename(os.path.expanduser(args.C))


    config = Configuration()

    if args.directory is not None:
        config.set_destination(args.directory)

    path = config.destination

    if (not args.r):
        process_folder(path, path)
    else:
        for dirname, dirnames, filenames in os.walk(path):
            if not excluded_folder(dirname):
                logging.debug('dirname=%s, dirnames=%s, filenames=%s' % (dirname, dirnames, filenames))
                process_folder(dirname, path)
