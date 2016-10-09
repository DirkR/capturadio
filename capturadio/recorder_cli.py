#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""capturadio is a library to capture mp3 radio streams, process
the recorded media files and generate an podcast-like rss feed.

 * http://github.com/dirkr/capturadio
 * Repository and issue-tracker: https://github.com/dirkr/capturadio
 * Licensed under the public domain
 * Copyright (c) 2012- Dirk Ruediger <dirk@niebegeg.net>

recorder.py is the command line program to interact with capturadio.
"""
from __future__ import unicode_literals, print_function

import sys
import os
import re
import logging
import shelve

from docopt import docopt

from capturadio import Configuration, Recorder, Station, version_string as capturadio_version, app_folder
from capturadio.util import find_configuration, parse_duration
from capturadio.generator import generate_feed

logging.basicConfig(
    filename=os.path.join(app_folder, 'log'),
    format='[%(asctime)s] %(levelname)-6s %(module)s::%(funcName)s:%(lineno)d: %(message)s',
    level=logging.INFO,
)


def show_capture(*args):
    """Usage:
    recorder show capture [--duration=<duration>] [options]

Capture a show.

Options:
    --duration,-d=<duration> Set the duration, overrides show setting

Examples:
    1. Capture an episode of the show 'nighttalk'
        recorder show capture nighttalk

    2. Capture an episode of the show 'nighttalk', but only 35 minutes
        recorder show capture nighttalk -d 35m

    """
    config = Configuration()
    if len(config.stations) == 0:
        print('No stations defined, add stations at first!')
        sys.exit(0)

    if len(config.shows) == 0:
        print('No shows defined, add shows at first!')
        sys.exit(0)
    args = args[0]
    if args['<show>'] in config.shows:
        show = config.shows[args['<show>']]
        try:
            recorder = Recorder()
            episode = recorder.capture(config, show)
            with shelve.open(os.path.join(app_folder, 'episodes_db')) as db:
                db[episode.slug] = episode
        except Exception as e:
            logging.error('Unable to capture recording: {}'.format(e))
    else:
        print('Unknown show %r' % args['<show>'])


def config_setup(args):
    """Usage:
    recorder config setup [ -u | -p ]

Setup program settings. A new settings file is created.

Options:
    -u        Create user settings in ~/.capturadio
    -p        Crete local settings in current work directory

    """
    config = Configuration()
    bbcradio2 = config.add_station(
        'bbc2',
        'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio2_mf_p?s=1423688987&e=1423703387&h=1f97ff4f9b0e0f1ae988bdf684f233b3',
        'BBC Radio 2',
        'http://www.bbc.co.uk/radio2/images/homepage/bbcradio2.gif'
    )
    bobharriscountry = config.add_show(
        bbcradio2,
        'bobharriscountry',
        'Bob Harris Country',
        parse_duration('58m'),
    )
    bobharriscountry.link_url = 'http://www.bbc.co.uk/programmes/b006x527'
    bobharrissunday = config.add_show(
        bbcradio2,
        'bobharrissunday',
        'Bob Harris Sunday',
        parse_duration('2h57m'),
    )
    bobharrissunday.link_url = 'http://www.bbc.co.uk/programmes/b006wqtf'
    config.write_config()
    print("""
Created a new configuration at %(filename)s.
The URL is set to %(url)s and the files
are stored at %(destination)s.
You can change all settings by editing %(filename)s
and you are engcouraged to do that.

Use the command 'config list' to see all settings.""" % {
        'destination': config.destination,
        'filename': config.filename,
        'url': config.feed['base_url'],
    }
          )


def config_list(args):
    """Usage:
    recorder config list

Show program settings.

    """
    config = Configuration()

    print("%s: %s" % ('Configutation file', config.filename))
    for key in ['destination', 'date_pattern', 'comment_pattern', 'folder',
                'filename', 'tempdir']:
        val = config._shared_state[key]
        if key == 'comment_pattern':
            val = val.replace('\n', '\n      ')
        print("%s: %s" % (key, val))

    for key, val in config._shared_state['feed'].items():
        print("feed.%s: %s" % (key, val))

    show_ids = config.shows.keys()
    station_ids = config.stations.keys()
    print('stations: %s' % ', '.join(station_ids) if len(station_ids)
          else 'No stations defined')
    print('shows: %s' % ', '.join(show_ids) if len(show_ids)
          else 'No shows defined')


def ignore_folder(dirname, patterns=['.git', '.bzr', 'svn', '.svn', '.hg']):
    for p in patterns:
        pattern = r'.*%s%s$|.*%s%s%s.*' % (os.sep, p, os.sep, p, os.sep)
        if re.match(pattern, dirname) is not None:
            return True
    return False


def feed_update(args):
    """Usage:
    recorder feed update

Generate rss feed files.

    """
    config = Configuration()
    root = Station(config, 'root', None, 'All recordings')
    root.filename = config.destination
    root.slug = ''

    with shelve.open(os.path.join(app_folder, 'episodes_db')) as db:
        generate_feed(config, db, root)
        for station in config.stations.values():
            generate_feed(config, db, station)
            for show in station.shows:
                generate_feed(config, db, show)

def help(args):
    cmd = r'%s_%s' % (args['<command>'], args['<action>'])
    try:
        print(globals()[cmd].__doc__)
    except KeyError:
        exit("%r is not a valid command. See 'recorder help'." %
             cmd.replace('_', ' '))


def find_command(args):
    if not args['help']:
        for command in ['feed', 'config', 'show']:
            if args[command]:
                for action in ['list', 'update', 'capture', 'show', 'setup']:
                    if args[action]:
                        return r'%s_%s' % (command, action)
    return 'help'


def main(argv=None):
    """
capturadio - Capture internet radio broadcasts in mp3 encoding format.

Usage:
    recorder.py help <command> <action>
    recorder.py show capture <show>
    recorder.py config list
    recorder.py config setup
    recorder.py feed update

General Options:
    -h, --help        show this screen and exit
    --version         Show version and exit.

Commands:
    show capture      Capture an episode of a show
    config setup      Create configuration file
    config list       Show configuration values
    feed update       Update rss feed files

See 'recorder.py help <command>' for more information on a specific command."""

    args = docopt(
        main.__doc__,
        version=capturadio_version,
        options_first=True,
        argv=argv or sys.argv[1:]
    )

    if len(sys.argv) == 1:
        sys.argv.append('--help')

    config_location = find_configuration()
    Configuration.folder = os.path.dirname(config_location)
    Configuration.filename = os.path.basename(config_location)
    if not os.path.exists(config_location):
        Configuration().write_config()

    try:
        cmd = find_command(args)
        method = globals()[cmd]
        assert callable(method)
    except (KeyError, AssertionError):
        exit("%r is not a valid command. See 'recorder help'." %
             cmd.replace('_', ' '))

    try:
        method(args)
    except RuntimeError as e:
      exit("ERROR: {}".format(e.message))


if __name__ == "__main__":
    main()
