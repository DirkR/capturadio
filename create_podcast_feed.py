#!/usr/bin/env python2.7
# This script traverses a directory tree and creates a rss file in the root folder
# containing all found mp3 files as items
# Original found at
# Found at http://snippsnapp.polite.se/wiki?action=browse&diff=0&id=PyPodcastGen
# and adopted for my needs

import datetime, urlparse, urllib, string, os, time, logging
import PyRSS2Gen
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import xml.dom.minidom
from capturadio import Configuration, Station, Show, format_date

logging.basicConfig(
	filename = os.path.expanduser('~/.capturadio/log'),
	level = logging.DEBUG,
)

# Taken from http://stackoverflow.com/questions/120951/how-can-i-normalize-a-url-in-python
def url_fix(s, charset='utf-8'):
	"""Sometimes you get an URL by a user that just isn't a real
	URL because it contains unsafe characters like ' ' and so on.  This
	function can fix some of the problems in a similar way browsers
	handle data entered by the user:
	
	:param charset: The target charset for the URL if the url was
					given as unicode string.
	"""
	if isinstance(s, unicode):
		s = s.encode(charset, 'ignore')

	scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
	path = urllib.quote(path, '/%')
	qs = urllib.quote_plus(qs, ':&=')
	return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))

class CaptuRadioRSS(PyRSS2Gen.RSS2):
	"""This class adds the "itunes" extension (<itunes:image>, etc.) to the rss feed."""

	rss_attrs = {
		"xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
		"version": "2.0",
	}

	def publish_extensions(self, handler):
		# implement this method to embed the <itunes:*> elements into the channel header.
		if self.image is not None and isinstance(self.image, PyRSS2Gen.Image) and self.image.url is not None:
			handler.startElement('itunes:image',  {'href': self.image.url})
			handler.endElement('itunes:image')

class CaptuRadioRSSItem(PyRSS2Gen.RSSItem):
	"""This class adds the "itunes" extension (<itunes:image>, etc.) to the rss feed item."""

	def publish_extensions(self, handler):
		# implement this method to embed the <itunes:*> elements into the channel header.
		if self.image is not None and isinstance(self.image, PyRSS2Gen.Image) and self.image.url is not None:
			handler.startElement('itunes:image',  {'href': self.image.url})
			handler.endElement('itunes:image')

class Audiofile:
	def __init__(self, collection, basename):
		self.config = collection.config

		self.log = logging.getLogger('create_podcast_feed.Audiofile')

		self.basename = string.replace(basename, collection.dirname, '', 1)
		if (os.path.isabs(self.basename)):
			self.basename = string.replace(self.basename, '/', '', 1)
		self.path = os.path.join(collection.dirname, basename)
		self.link = urlparse.urljoin(collection.urlbase, url_fix(self.basename))

		audio = MP3(self.path, ID3=EasyID3)

		try:
			self.title = audio['title'][0]
		except KeyError, e:
			self.title = basename[:-4]

		try:
			self.show = audio['album'][0]
		except KeyError, e:
			self.show = basename[:-4]

		try:
			self.date = audio['date'][0]
		except KeyError, e:
			self.date = format_date(self.config.date_pattern, time.time())

		try:
			self.artist = audio['artist'][0]
		except KeyError, e:
			self.artist = self.show

		try:
			self.playtime = audio.info.length
		except:
			self.playtime = 0

		try:
			self.copyright = audio['copyright'][0]
		except KeyError, e:
			self.copyright = self.artist


		self.description = u'Show: %s, Episode: %s, Copyright: %s %s' % (self.show, self.title, self.date, self.copyright)

		self.guid = PyRSS2Gen.Guid(self.link)
		self.size = os.path.getsize(self.path)
		self.enclosure = PyRSS2Gen.Enclosure(self.link, self.playtime, "audio/mpeg")
		self.pubdate = datetime.datetime.fromtimestamp(os.path.getmtime(self.path))

class Audiofiles:
	"""
	A collection of audiofiles and some metadata, used as the basis for at 
	
	"""

	def __init__(self, config, local_path = None):
		self.log = logging.getLogger('create_podcast_feed.Audiofiles')

		feed_title = config.feed['title']
		if (local_path != ''):
			feed_title += " - " + string.replace(local_path, '/', ' - ')


		self.config = config
		self.title = feed_title
		self.link = config.feed['about_url']
		self.description = config.feed['description']
		self.language =  config.feed['language']
		if local_path is None:
			self.urlbase = config.feed['base_url']
		else:
			self.urlbase = config.feed['base_url'] + urllib.quote(local_path)
		if not self.urlbase.endswith('/'):
			self.urlbase += '/'
		
		self.data = []

		self.generator = PyRSS2Gen._generator_name

	def append(self,audiofile):
		self.data.append(audiofile)

	def readfolder(self, dirname):
		self.log.info(u'readfolder: processing %s' % dirname)
		self.dirname = dirname
		for dirname, dirnames, filenames in os.walk(dirname):
			for filename in filenames:
				path = os.path.join(dirname, filename)
				if os.path.exists(path) and os.path.isfile(path) and path.endswith(".mp3"):
					if (path.startswith(u'./')):
						path = path[2:]
					audiofile = Audiofile(self, path)
					self.append(audiofile)

	def rssitems(self,n=10):
		result = []
		for audiofile in self.data:
			rssitem = CaptuRadioRSSItem(
				title = audiofile.title,
				link = audiofile.link,
                author = audiofile.artist,
				description = audiofile.description,
				guid = audiofile.guid,
				pubDate = audiofile.pubdate,
				enclosure = audiofile.enclosure
			)
			rssitem.image = self._create_image_tag(rssitem)
			result.append(rssitem)

		waste = [(i.pubDate,i) for i in result]
		waste.sort()
		waste.reverse()
		waste = waste[:n]
		result = [pair[1] for pair in waste]

		self.log.debug(u'rssitems: Found %d items' % len(result))
		return result

	def getrss(self):
		items = self.rssitems()
		channel = CaptuRadioRSS(title = self.title,
							  link = self.link,
							  description = self.description,
							  language = self.language,
							  generator = self.generator,
							  lastBuildDate = datetime.datetime.now(),                         
							  items = items)
		if len(items) > 0:
			channel.image = self._create_image_tag(items[0])
		return channel

	def _create_image_tag(self, rssitem):
		logo_url = self._get_logo_url(rssitem.author)
		if logo_url is not None:
			return PyRSS2Gen.Image(url = logo_url, title = rssitem.author, link = logo_url)
		else:
			return PyRSS2Gen.Image(url = self.config.default_logo_url, title = rssitem.author, link = logo_url)

	def _get_logo_url(self, station_name):
		self.log.debug(u'_get_logo_url: station_name=%s' % station_name)
		for id, station in self.config.stations.items():
			if station_name == station.name:
				self.log.debug(u'_get_logo_url: found %s' % station.logo_url)
				return station.logo_url
		self.log.debug(u'_get_logo_url: found noting')
		return None

def process_folder(path, root_path):
	local_path = string.replace(path, root_path, '')
	if (local_path != ''):
		if (local_path.startswith('/')):
			local_path = local_path[1:]
		if (not local_path.endswith('/')):
			local_path += '/'

	audiofiles = Audiofiles(config, local_path)
	audiofiles.readfolder(path)

	rss_file = config.feed['file_name']

	rss = audiofiles.getrss()
	rss.write_xml(open(os.path.join(path, rss_file), "w"))


if __name__ == "__main__":
	import argparse

	config = Configuration()

	parser = argparse.ArgumentParser(description='Generate a rss file containing all mp3 files in this directory and all sub directories.')
	parser.add_argument('-r', action='store_true', help="Put an rss file into every subfolder, that contains all episodes in all of it's subfolders.")
	parser.add_argument('directory', nargs='?', help='The directory to be indexed. Use current directory if ommitted.')
	args = parser.parse_args()

	if args.directory is not None:
		config.set_destination(os.path.expanduser(args.directory))

	path = config.destination

	if (not args.r):
		process_folder(path, path)
	else:
		for dirname, dirnames, filenames in os.walk(path):
			process_folder(dirname, path)
