#!/usr/bin/env python2.7
# -*- coding: utf_8 -*-
"""capturadio - Capture internet radio programs broadcasted in mp3 encoding format.

Usage:
  recorder.py [-d destination] [-C configfile] -l length -s station -b title [-t title]
  recorder.py [-d destination] [-C configfile] -S show [-l length] [-t title]

Options:
  -h, --help                       show this screen and exit
  -d folder, --destination folder  Destination directory
  -C file, --config file           Configuration file

  -l duration, --length duration   Length of recording in seconds
  -s station, --station station    Name of the station, defined in ~/.capturadio/capturadiorc.
  -b title, --broadcast title      Title of the show
  -t title, --title title          Title of the episode

  -S show, --show show             ID of the show, has to be defined in configuration file"""

import sys, os
from docopt import docopt
from capturadio import Configuration, Station, Show, Recorder, version_string
from capturadio.util import parse_duration

if __name__ == "__main__":
    args = docopt(__doc__, version=version_string)

    if len(sys.argv) == 1:
        sys.argv.append('--help')

    if args['--config'] is not None:
        if not os.path.exists(os.path.expanduser(args['--config'])):
            print('Configuration file "%s" does not exist' % args['--config'])
            sys.exit(1)
        Configuration.configuration_folder = os.path.dirname(os.path.expanduser(args['--config']))
        Configuration.filename = os.path.basename(os.path.expanduser(args['--config']))

    try:
      config = Configuration()
    except IOError, e:
      print('Configuration could not be loaded: %s' % e.reason)
      sys.exit(1)

    if len(config.stations) == 0:
      print('No stations defined, add stations at first!')
      sys.exit(0)

    if len(config.shows) == 0:
      print('No shows defined, add shows at first!')
      sys.exit(0)

    if args['--show'] is not None:
        show_ids = map(lambda id: id.encode('ascii'), config.shows.keys())
        if args['--show'] not in config.shows.keys():
            print "Show '%s' is unknown. Use one of these: %s." % (args['--show'], ', '.join(show_ids))
            exit(1)
        show = config.shows[args['--show']]
        if args['--title'] is not None:
            show.name = u'%s' % unicode(args['--title'], 'utf8')
        if args['--length'] is not None:
            duration = parse_duration(args['--length'])
            if duration < 1:
                print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
                exit(1)
            show.duration = duration
    else:
        duration = parse_duration(args['--length'])
        if duration < 1:
            print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
            exit(1)

        if args['--destination'] is not None:
            config.set_destination(os.path.expanduser(args['--destination']))

        if args['--station'] not in config.get_station_ids():
            print "Station '%s' is unknown. Use one of these: %s." % (args['--station'], ', '.join(config.get_station_ids()))
            exit(1)
        station = config.stations[str.lower(args['--station'])]

        title = u'%s' % unicode(args['--title'] if (args['--title'] is not None) else args['--broadcast'], 'utf8')
        show = config.add_show(station, title, title, duration)

    try:
      recorder = Recorder()
      recorder.capture(show)
    except Exception, e:
      print('Unable to capture recording: %s' % e.reason)
