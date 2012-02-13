#!/usr/bin/env python2.7
# -*- coding: utf_8 -*-

import urllib2
import time
import argparse
import os
import logging

def format_date(time_value):
	if (config.has_section('settings') and config.has_option('settings', 'date_pattern')):
		pattern = config.get('settings', 'date_pattern', '%Y-%m-%d_%H-%M-%S')
	else:
		pattern = '%Y-%m-%d_%H-%M-%S'

	if (type(time_value).__name__ == 'float'):
		time_value = time.localtime(time_value)
	elif (type(time_value).__name__ == 'struct_time'):
		pass
	else:
		raise TypeError('time_value has to be a struct_time or a float. "%s" given.' % time_value)
	return time.strftime(pattern, time_value)

class Configuration:
	filename = '~/.capturadio/capturadiorc'

	def __init__(self):
		self.stations = {}
		self.shows = {}
		self.default_logo_url = None
		self.__load_config()
		self.destination = os.getcwd()
		self.date_pattern = "%Y-%m-%d %H:%M"

	def __load_config(self):
		import ConfigParser
		config = ConfigParser.ConfigParser()
		config.read([os.path.expanduser(Configuration.filename)])

		if config.has_section('settings'):
			if config.has_option('settings', 'destination'):
				self.destination = os.path.expanduser(config.get('settings', 'destination'))
			if config.has_option('settings', 'date_pattern'):
				self.date_pattern = os.path.expanduser(config.get('settings', 'date_pattern'))

		if config.has_section('feed'):
			if config.has_option('feed', 'default_logo_url'):
				self.default_logo_url = config.get('feed', 'default_logo_url')

		if config.has_section('stations'):
			for station_id in config.options('stations'):
				station_stream = config.get('stations', station_id)
				station_name = station_id
				station_logo_url = self.default_logo_url
				if config.has_section(station_id):
					if config.has_option(station_id, 'name'):
						station_name = config.get(station_id, 'name')
					if config.has_option(station_id, 'logo_url'):
						station_logo_url = config.get(station_id, 'logo_url')
				self.add_station(station_id, station_stream, station_name, station_logo_url)

	def __repr__(self):
		return "%s(%r)" % (self.__class__, self.__dict__)


	def get_station_ids(self):
		if self.stations is not None:
			return self.stations.keys()
		else:
			return None

	def set_default_logo_url(self, url):
		self.default_logo_url = url

	def add_station(self, id, stream_url, name = None, logo_url = None):
		self.stations[id] = Station(id, stream_url, name, logo_url)

	def add_show(self, station, id, name, logo = None):
		if not isinstance(station, Station):
			raise TypeError('station has to be of type "Station"')
		show = Show(station, id, name, logo)
		self.shows[id] = show

	def find_station_by_id(self, id):
		if id in self.stations:
			return self.stations[id]
		return None

	def find_show_by_id(self, id):
		if id in self.shows:
			return self.shows[id]
		return None

	def find_showlogo_by_id(self, id):
		if id not in self.shows:
			raise "Show is not registered in ShowRegistry"
		show = self.shows[id]
		if show.logo_url is not None:
			return show.logo_url

		station = show.station
		if station.logo_url is not None:
			return station.logo_url

		return self.default_logo


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

	def __init__(self, station, id, name, logo_url = None):
		if not isinstance(station, Station):
			raise TypeError('station has to be of type "Station"')

		self.station = station
		self.id = id
		self.name = name
		self.logo_url = logo_url
		station.shows.append(self)

	def __repr__(self):
		return "%s(%r)" % (self.__class__, self.__dict__)

class Recorder:
	log = None

	def __init__(self, config, show, episode_title = ''):
		logging.basicConfig(
			filename = os.path.expanduser('~/.capturadio/log'),
			level = logging.DEBUG,
		)
		self.log = logging.getLogger('capturadio')

		self.stream_url = stream_url
		self.episode_title = unicode(episode_title, 'utf-8')
		self.show_title = unicode(show_title, 'utf-8')
		self.destination = os.getcwd()
		self.station_name = None
		self.station_logo = None
		self.file_name = None
		self.start_time = None

	def set_destination(self, destination):
		if (destination is not None and os.path.exists(destination) and os.path.isdir(destination)):
			if (destination.startswith(u'./')):
			    destination = destination[2:]
			if (not os.path.isabs(destination)):
			    destination = os.path.join(os.getcwd(), destination)

			self.destination = unicode(destination)

	def set_station_details(self, name, logo = None):
		self.station_name = unicode(name, 'utf-8')
		self.station_logo = unicode(logo)

	def capture(self, duration):
		self.log.info(u'capture "%s" from "%s" for %s seconds to %s' % \
				(self.episode_title, self.station_name, duration, self.destination))
		import tempfile
		self.start_time = time.time()
		self.file_name = u"%s/capturadio_%s.mp3" % (tempfile.gettempdir(), os.getpid())
		self._write_stream_to_file()
		self._copy_file_to_destination()
		self._add_metadata()

	def _write_stream_to_file(self):
		not_ready = True
		try:
			file = open(self.file_name, 'w+b')
			stream = urllib2.urlopen(self.stream_url);
			while not_ready:
				file.write(stream.read(10240));
				if ((time.time() - self.start_time) > duration):
					not_ready = False
			file.close
		except Exception as e:
			mesage= "Could not complete capturing, because an exception occured.", e
			self.log.error(message, e)
			print message
			os.remove(self.file_name)
			self.file_name = None

	def _copy_file_to_destination(self):
		import shutil, re

		time_string = format_date(time.localtime(self.start_time))
		target_file = u"%s/%s/%s/%s_%s.mp3" % \
			(self.destination,
			 self.station_name if self.station_name is not None else self.station_nick,
			 self.show_title,
			 self.episode_title,
			 time_string)
		target_file = re.compile(u'[^\w\d._/ -]').sub('', target_file)
		if (not os.path.isdir(os.path.dirname(target_file))):
			os.makedirs(os.path.dirname(target_file))
		shutil.copy2(self.file_name, target_file)

		self.file_name = target_file

	def _add_metadata(self):
		if self.file_name is None:
			raise "file_name is not set - you cannot add metadata to None"

		from mutagen.mp3 import MP3
		import mutagen.id3
		date = time.strftime('%Y', time.localtime(self.start_time))
		comment = u'Show: %s\nEpisode: %s\nCopyright: %s %s' % (self.show_title, self.episode_title, date, self.station_name)

		audio = MP3(self.file_name)
		# See http://www.id3.org/id3v2.3.0 for details about the ID3 tags
		audio["TIT2"] = mutagen.id3.TIT2(encoding=2, text=[self.episode_title])
		audio["TDRC"] = mutagen.id3.TDRC(encoding=2, text=[format_date(self.start_time)])
		audio["TCON"] = mutagen.id3.TCON(encoding=2, text=[u'Podcast'])
		audio["TALB"] = mutagen.id3.TALB(encoding=2, text=[self.show_title])
		audio["TLEN"] = mutagen.id3.TLEN(encoding=2, text=[duration * 1000])
		audio["TPE1"] = mutagen.id3.TPE1(encoding=2, text=[self.station_name])
		audio["TCOP"] = mutagen.id3.TCOP(encoding=2, text=[self.station_name])
		audio["COMM"] = mutagen.id3.COMM(encoding=2, text=[comment])
		self._add_logo(audio)
		audio.save()

	def _add_logo(self, audio):
		from mutagen.id3 import APIC
		# APIC part taken from http://mamu.backmeister.name/praxis-tipps/pythonmutagen-audiodateien-mit-bildern-versehen/
		if self.station_logo is not None:
			request = urllib2.Request(self.station_logo)
			request.get_method = lambda : 'HEAD'
			try:
				response = urllib2.urlopen(request)
				logo_type = response.info().gettype()

				if logo_type in ['image/jpeg', 'image/png']:
					img_data  = urllib2.urlopen(self.station_logo).read()
					img = APIC(
						encoding = 3, # 3 is for utf-8
						mime = logo_type,
						type = 3, # 3 is for the cover image
						desc = u'Station logo',
						data = img_data
					)
					audio.tags.add(img)
			except urllib2.HTTPError, e:
				mesage= "Error during capturing"
				self.log.error(message, e)
				print message, e


if __name__ == "__main__":

	config = Configuration()

	parser = argparse.ArgumentParser(
		description='Capture internet radio programs broadcasted in mp3 encoding format.',
		epilog = "Here is a list of defined radio stations: %s" % config.get_station_ids()
	)
	parser.add_argument('-l', metavar='length', type=int, required=True, help='Length of recording in seconds')
	parser.add_argument('-s', metavar='station', required=True, help='Name of the station, defined in ~/.capturadio/capturadiorc.')
	parser.add_argument('-b', metavar='broadcast', required=True, help='Title of the broadcast')
	parser.add_argument('-t', metavar='title', required=False, help='Title of the recording')
	parser.add_argument('-d', metavar='destination', required=False, help='Destination directory')

	args = parser.parse_args()

	duration = args.l
	if (duration < 1):
	    print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
	    exit(1)

	if args.s not in config.get_station_ids():
	    print "Station '%s' is unknown. Use one of these: %s." % (args.s, config.get_station_ids())
	    exit(1)
	else:
		station = config.find_station_by_id(args.s)

	title = args.t if (args.t is not None) else args.b

	if args.d is not None:
		config.destination = os.path.expanduser(args.d)

	recorder = Recorder(config, show, title)
	recorder.set_destination(destination)

	if (config.has_section(station)):
		station_name = station_logo = None
		if (config.has_option(station, 'name')):
			station_name = config.get(station, 'name')
		if (config.has_option(station, 'logo')):
			station_logo = config.get(station, 'logo')
		recorder.set_station_details(name = station_name, logo = station_logo)

	recorder.capture(duration)
