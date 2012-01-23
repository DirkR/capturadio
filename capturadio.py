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

def add_metadata(file, station_name, broadcast, title):
	from mutagen.mp3 import MP3
	from mutagen.id3 import ID3, TIT2, TCON, TDRC, TALB, APIC
	if (config.has_section(station_name) and config.has_option(station_name, 'name')):
		station_name = config.get(station_name, 'name', station_name)

	audio = MP3(file)
	audio["TIT2"] = TIT2(encoding=3, text=[title])
	audio["TCON"] = TCON(encoding=3, text=['Podcast'])
	audio["TDRC"] = TDRC(encoding=3, text=[time.strftime('%Y')])
	audio["TALB"] = TALB(encoding=3, text=[broadcast])
	
#	if (config.has_section(station_name) and config.has_option(station_name, 'logo')):
#		logo = config.get(station_name, 'logo')
#		audio["APIC"] = APIC(encoding=0, data=['Podcast'])	
	audio.save()

def store_file(src_file, destination, station_name, artist, title):
	import shutil, re
	if (config.has_section(station_name) and config.has_option(station_name, 'name')):
		station_name = config.get(station_name, 'name', station_name)

	target_file = "%s/%s/%s/%s_%s.mp3" % (destination, station_name, artist, title, time.strftime("%Y-%m-%d"))
	target_file = re.sub("[^\w\d._/ -]", "", target_file)
	if (not os.path.isdir(os.path.dirname(target_file))):
		os.makedirs(os.path.dirname(target_file))
	print "copy %s to %s" % (src_file, target_file)
	shutil.copy2(src_file, target_file)
	return target_file

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.capturadiorc')])

parser = argparse.ArgumentParser(description='Capture internet radio programs broadcasted in mp3 encoding format.')
parser.add_argument('-l', metavar='length', type=int, required=True, help='Length of recording in seconds')
parser.add_argument('-s', metavar='station', required=True, help='Name of the station, defined in ~/.capturadiorc. %s' % config.sections())
parser.add_argument('-b', metavar='broadcast', required=True, help='Title of the broadcast')
parser.add_argument('-t', metavar='title', required=False, help='Title of the recording')
parser.add_argument('-d', metavar='destination', required=False, help='Destination directory')

args = parser.parse_args()

duration = args.l
if (duration < 1):
    print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
    exit(1)

station = args.s
if (not config.has_option('stations', station)):
    print "Station '%s' is unknown. Use one of these: %s." % (station, config.sections())
    exit(1)

title = args.t if (args.t != None) else args.b

if (args.d != None):
	destination = args.d
elif(config.has_section('settings') and config.has_option('settings', 'destination')):
	destination = config.get('settings', 'destination')
else:
	destination = os.getcwd()

file = capture(config.get('stations', station), duration)

file = store_file(file, destination, station, args.b, title)
add_metadata(file, station, args.b, title)