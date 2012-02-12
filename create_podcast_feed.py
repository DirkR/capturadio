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

logging.basicConfig(
	filename = os.path.expanduser('~/.capturadio/log'),
	level = logging.DEBUG,
)

def format_date(time_value):
	if (config.has_section('settings') and config.has_option('settings', 'date_pattern')):
		pattern = config.get('settings', 'date_pattern', '%Y-%m-%d_%H-%M-%S')
	else:
		pattern = '%Y-%m-%d_%H-%M-%S'

	if (type(time_value).__name__=='float'):
		time_value = time.localtime(time_value)
	elif (type(time_value).__name__=='struct_time'):
		pass
	else:
		raise TypeError('time_value has to be a struct_time or a float. "%s" given.' % time_value)
	return time.strftime(pattern, time_value)

def as_utf8(string):
	return u'%s' % unicode(string, 'utf-8')

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
		if self.image is not None and type(self.image) is 'Image':
			PyRSS2Gen._opt_element(handler, "itunes:image", self.image.url)

class Audiofile:
	def __init__(self, collection, basename):
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
			self.date = format_date(time.time())

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

	def __init__(self,urlbase,title, link, description, language):
		self.log = logging.getLogger('create_podcast_feed.Audiofiles')

		self.urlbase = urlbase
		self.title = title
		self.link = link
		self.description = description
		self.language = language
		
		self.data = []

		self.generator = PyRSS2Gen._generator_name        

	def append(self,audiofile):
		self.data.append(audiofile)

	def readfolder(self, dirname):
		self.log.info(u'readfolder: processing %s' % dirname)
		self.dirname = as_utf8(dirname)
		for dirname, dirnames, filenames in os.walk(dirname):
			for filename in filenames:
				path = as_utf8(os.path.join(dirname,filename))
				if os.path.exists(path) and os.path.isfile(path) and path.endswith(".mp3"):
					if (path.startswith(u'./')):
						path = path[2:]
					audiofile = Audiofile(self, path)
					self.append(audiofile)

	def rssitems(self,n=10):
		result = []
		for audiofile in self.data:

			rssitem = PyRSS2Gen.RSSItem(
				title = audiofile.title,
				link = audiofile.link,
                author = audiofile.artist,
				description = audiofile.description,
				guid = audiofile.guid,
				pubDate = audiofile.pubdate,
				enclosure = audiofile.enclosure
			)
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
			first_item = items[0]
			logo_url = self._get_logo_url(first_item.author)
			if logo_url is not None:
				channel.image = PyRSS2Gen.Image(url = logo_url, title = first_item.author, link = logo_url)
		return channel

	def _get_logo_url(self, station_name):
		self.log.debug(u'_get_logo_url: station_name=%s' % station_name)
		global station_logo_urls
		if station_logo_urls is None:
				station_logo_urls = {} # been here
				if config.has_section('stations'):
					for station in config.options('stations'):
						if (config.has_section(station) and
							config.has_option(station, 'name') and
							config.has_option(station, 'logo')):
								name = string.lower(config.get(station, 'name'))
								station_logo_urls[name] = config.get(station, 'logo')
		if string.lower(station_name) in station_logo_urls:
			self.log.debug(u'_get_logo_url: found %s' % station_logo_urls[string.lower(station_name)])
			return station_logo_urls[string.lower(station_name)]
		else:
			self.log.debug(u'_get_logo_url: found noting')
			return None

def process_folder(path, root_path):
	import ConfigParser

	local_path = string.replace(path, root_path, '')
	if (local_path != ''):
		if (local_path.startswith('/')):
			local_path = local_path[1:]
		if (not local_path.endswith('/')):
			local_path += '/'

	if (config.has_section('feed')):
		feed_title = config.get('feed', 'title', 'Internet radio recordings')
		feed_url = config.get('feed', 'url', 'http://example.org')
		if (not feed_url.endswith('/')):
			feed_url += "/"
		feed_description = config.get('feed', 'description', 'Recordings of internet radio station broadcastings')
		feed_about_url = config.get('feed', 'about_url',  feed_url + '/about')
		feed_language = config.get('feed', 'language',  'en')
	else:
		feed_title = 'Internet radio recordings'
		feed_url = 'http://example.org/'
		feed_description = 'Recordings of internet radio station broadcastings'
		feed_about_url = feed_url + 'about'
		feed_language = 'en'

	if (local_path != ''):
		feed_title += " - " + string.replace(local_path, '/', ' - ')

	audiofiles = Audiofiles(feed_url + urllib.quote(local_path),
							as_utf8(feed_title),
							feed_about_url,
							as_utf8(feed_description),
							feed_language)
	audiofiles.readfolder(path)

	if (config.has_section('feed')):
		rss_file = config.get('feed', 'filename',  'rss.xml')
	else:
		rss_file = 'rss.xml'

	rss = audiofiles.getrss()
	rss.write_xml(open(os.path.join(path, rss_file), "w"))


if __name__ == "__main__":
    import argparse
    import ConfigParser

    station_logo_urls = None


    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('~/.capturadio/capturadiorc'), os.path.expanduser('~/.capturadiorc')])

    parser = argparse.ArgumentParser(description='Generate a rss file containing all mp3 files in this directory and all sub directories.')
    parser.add_argument('-r', action='store_true', help="Put an rss file into every subfolder, that contains all episodes in all of it's subfolders.")
    parser.add_argument('directory', nargs='?', help='The directory to be indexed. Use current directory if ommitted.')
    args = parser.parse_args()


    if (args.directory != None and os.path.exists(args.directory) and os.path.isdir(args.directory)):
        path = args.directory
        if (path.startswith('./')):
            path = path[2:]
        if (not os.path.isabs(path)):
            path = os.path.join(os.getcwd(), path)
    elif(config.has_section('settings') and config.has_option('settings', 'destination')):
        path = os.path.expanduser(config.get('settings', 'destination'))
    else:
        path = os.getcwd()

    if (not args.r):
        process_folder(path, path)
    else:
        for dirname, dirnames, filenames in os.walk(path):
            process_folder(dirname, path)
