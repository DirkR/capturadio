#!/usr/bin/env python2.7
# This script traverses a directory tree and creates a rss file in the root
# folder containing all found mp3 files as items
# Original found at
# http://snippsnapp.polite.se/wiki?action=browse&diff=0&id=PyPodcastGen
# and adopted for my needs

import os
import logging
import argparse
import re
from capturadio import Configuration
from capturadio.rss import Audiofiles


def process_folder(path, root_path):
    log = logging.getLogger('create_podcast_feed')
    log.debug('exec process_folder(path=%s, root_path=%s)' % (path, root_path))

    local_path = path.replace(root_path, '')
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


def excluded_folder(dirname, patterns=['.git', '.bzr', 'svn', '.svn', '.hg']):
    for p in patterns:
        pattern = r'.*%s%s$|.*%s%s%s.*' % (os.sep, p, os.sep, p, os.sep)
        if re.match(pattern, dirname) is not None:
            return True
    return False


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
        process_folder(path, path)
    else:
        for dirname, dirnames, filenames in os.walk(path):
            if not excluded_folder(dirname):
                logging.debug(
                    'dirname=%s, dirnames=%s, filenames=%s' % (
                        dirname,
                        dirnames,
                        filenames)
                )
                process_folder(dirname, path)
