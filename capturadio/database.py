"""capturadio is a library to capture mp3 radio streams, process
the recorded media files and generate an podcast-like rss feed.

 * Copyright (c) 2012- Dirk Ruediger <dirk@niebegeg.net>

The module capturadio.database provides a simple database backend, based on the
shelve module.
"""
# -*- coding: utf-8 -*-
import shelve
import os
import fcntl
import types
import builtins
from fcntl import LOCK_SH, LOCK_EX, LOCK_UN, LOCK_NB

from capturadio import app_folder


# Based on: https://code.activestate.com/recipes/576591-simple-shelve-with-linux-file-locking/
def _close(self):
    shelve.Shelf.close(self)
    fcntl.flock(self.lckfile.fileno(), LOCK_UN)
    self.lckfile.close()


# Based on: https://code.activestate.com/recipes/576591-simple-shelve-with-linux-file-locking/
def open(dbname, flag='c', protocol=None, writeback=False, block=True):
    """Open the sheve file, createing a lockfile at filename.lck.  If
    block is False then a IOError will be raised if the lock cannot
    be acquired"""
    filename = os.path.join(app_folder, dbname)
    lckfilename = filename + ".lck"
    lckfile = builtins.open(lckfilename, 'w')

    # Accquire the lock
    if flag == 'r':
        lockflags = LOCK_SH
    else:
        lockflags = LOCK_EX
    if not block:
        lockflags = LOCK_NB
    fcntl.flock(lckfile.fileno(), lockflags)

    # Open the shelf
    shelf = shelve.open(filename, flag, protocol, writeback)

    # Override close
    shelf.close = types.MethodType(_close, shelf)
    shelf.lckfile = lckfile

    # And return it
    return shelf
