#!/usr/bin/env python
import urllib2
import time
import argparse
import ConfigParser
import os

def capture(stream_url, duration):
	import tempfile
	file_name = "%s/capturadio_%s.mp3" % (tempfile.gettempdir(), os.getpid())
	file = open(file_name, 'w+b')
	start_time = time.time()
	not_ready = True
	stream = urllib2.urlopen(stream_url);
	while not_ready:
		file.write(stream.read(10240));
		if ((time.time() - start_time) > duration):
			not_ready = False
	file.close
	return file_name

def add_metadata(src_file, station_name, artist, title):
	import shutil, re
	target_file = "./%s/%s/%s_%s.mp3" % (station_name, artist, title, time.strftime("%Y-%m-%d"))
	target_file = re.sub("[^\w\d._/ -]", "", target_file)
	if (not os.path.isdir(os.path.dirname(target_file))):
		os.makedirs(os.path.dirname(target_file))
	print "copy %s to %s" % (src_file, target_file)
	shutil.copy2(src_file, target_file)

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.capturadiorc')])

usage="Usage: $0: [-l length] [-u url|-s station] [-a Artist] [-t title] [-d destination] args";

parser = argparse.ArgumentParser(description='Capture internet radio programs broadcasted in mp3 encoding format.')
parser.add_argument('-l', metavar='length', type=int, required=True, help='Length of recording in seconds')
parser.add_argument('-s', metavar='station', required=True, help='Name of the station, defined in ~/.capturadiorc. %s' % config.sections())
parser.add_argument('-a', metavar='artist', required=True, help='Title of the artist')
parser.add_argument('-t', metavar='title', required=True, help='Title of the recording')

args = parser.parse_args()

duration = args.l
if (duration < 1):
    print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
    exit(1)

station = args.s
if (station not in config.sections()):
    print "Station '%s' is unknown. Use one of these: %s." % (station, config.sections())
    exit(1)
if (not config.has_option(station, 'url')):
    print "Station '%s' has no url defined. Please edit your ~/.capturadiorc file." % (station)
    exit(1)

file = capture(config.get(station, 'url'), duration)
add_metadata(file, station, args.a, args.t)