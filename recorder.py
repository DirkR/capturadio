#!/usr/bin/env python2.7
# -*- coding: utf_8 -*-
import sys
import os
from docopt import docopt
from capturadio import Configuration, Recorder, version_string

config_locations = [
    os.path.join(os.getcwd(), 'capturadiorc'),
    os.path.expanduser('~/.capturadio/capturadiorc'),
    os.path.expanduser('~/.capturadiorc'),
    os.path.join('/etc', 'capturadiorc'),
]


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
    if args[0] in config.shows:
        show = config.shows[args[0]]
        try:
            recorder = Recorder()
            recorder.capture(show)
        except Exception as e:
            print('Unable to capture recording: %s' % e)
    else:
        print('Unknown show %r' % args[0])


def config_show(args):
    """Usage:
    recorder config show

Show program settings.

    """
    config = Configuration()

    for key in ['destination', 'date_pattern', 'comment_pattern', 'folder',
                'filename', 'tempdir', 'default_logo_url']:
        val = Configuration._shared_state[key]
        if key == 'comment_pattern':
            val = val.replace('\n', '\n      ')
        print u"%s: %s" % (key, val)

    for key, val in Configuration._shared_state['feed'].items():
        print u"feed_%s: %s" % (key, val)


def help(argv):
    if len(argv) == 1:
        cmd = argv[0]
        try:
            print(globals()[cmd].__doc__)
        except KeyError:
            exit("%r is not a tag command. See 'tag help'." % cmd)
    else:
        docopt(main.__doc__, argv='-h')


def main(argv=None):
    """
capturadio - Capture internet radio programs broadcasted in mp3 encoding format.

Usage:
    recorder.py help <command> <action>
    recorder.py <command> <action> [<options>...]

General Options:
    -h, --help        show this screen and exit
    --version         Show version and exit.

Commands:
    show capture      Capture an episode of a show
    config show       Show configuration

See 'recorder.py help <command>' for more information on a specific command."""

    args = docopt(main.__doc__,
                  version=version_string,
                  options_first=True,
                  argv=argv or sys.argv[1:])

    if len(sys.argv) == 1:
        sys.argv.append('--help')

    for location in config_locations:
        if os.path.exists(location):
            Configuration.configuration_folder = os.path.dirname(location)
            Configuration.filename = os.path.basename(location)
            break
    else:
        print('No configuration file found')
        sys.exit(1)

    try:
        config = Configuration()
    except IOError, e:
        print('Configuration could not be loaded: %s' % e)
        sys.exit(1)

    try:
        if args['help']:
            cmd = 'help'
            options = [ r'%s_%s' % (args['<command>'], args['<action>']) ]
        else:
            cmd = r'%s_%s' % (args['<command>'], args['<action>'])
            options = args['<options>']
        method = globals()[cmd]
        assert callable(method)
    except (KeyError, AssertionError):
        exit("%r is not a recorder command. See 'recorder help'." % cmd.replace('_', ' '))

    method(options)

#    if len(config.stations) == 0:
#        print('No stations defined, add stations at first!')
#        sys.exit(0)
#
#    if len(config.shows) == 0:
#        print('No shows defined, add shows at first!')
#        sys.exit(0)
#
#    if args['--show'] is not None:
#        show_ids = map(lambda id: id.encode('ascii'), config.shows.keys())
#        if args['--show'] not in config.shows.keys():
#            print "Show '%s' is unknown. Use one of these: %s." % (args['--show'], ', '.join(show_ids))
#            exit(1)
#        show = config.shows[args['--show']]
#        if args['--title'] is not None:
#            show.name = u'%s' % unicode(args['--title'], 'utf8')
#        if args['--length'] is not None:
#            duration = parse_duration(args['--length'])
#            if duration < 1:
#                print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
#                exit(1)
#            show.duration = duration
#    else:
#        duration = parse_duration(args['--length'])
#        if duration < 1:
#            print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
#            exit(1)
#
#        if args['--destination'] is not None:
#            config.set_destination(os.path.expanduser(args['--destination']))
#
#        if args['--station'] not in config.get_station_ids():
#            print "Station '%s' is unknown. Use one of these: %s." % (args['--station'], ', '.join(config.get_station_ids()))
#            exit(1)
#        station = config.stations[str.lower(args['--station'])]
#
#        title = u'%s' % unicode(args['--title'] if (args['--title'] is not None) else args['--broadcast'], 'utf8')
#        show = config.add_show(station, title, title, duration)
#
#

if __name__ == "__main__":
    main()
