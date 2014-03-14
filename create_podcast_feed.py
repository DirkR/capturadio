#!/usr/bin/env python2.7
# This script traverses a directory tree and creates a rss file in the root
# folder containing all found mp3 files as items
# Original found at
# http://snippsnapp.polite.se/wiki?action=browse&diff=0&id=PyPodcastGen
# and adopted for my needs

import os
import logging
import argparse
from capturadio import Configuration
from capturadio.rss import Audiofiles


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='''Generate a rss file containing all mp3 files
        in this directory and all sub directories.''')
    parser.add_argument(
        '-C',
        metavar='configfile',
        required=False, help='Configuration file'
    )
    parser.add_argument(
        '-r',
        action='store_true',
        help='''Put an rss file into every subfolder, that contains
        all episodes in all of it's subfolders.'''
    )
    parser.add_argument(
        'directory',
        nargs='?',
        help='The directory to be indexed. Use current directory if ommitted.'
    )
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
        Audiofiles.process_folder(path, path)
    else:
        for dirname, dirnames, filenames in os.walk(path):
            if not Audiofiles.excluded_folder(dirname):
                logging.debug(
                    'dirname=%s, dirnames=%s, filenames=%s' % (
                        dirname,
                        dirnames,
                        filenames)
                )
                Audiofiles.process_folder(dirname, path)
