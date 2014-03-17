#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recorder import ignore_folder

def test_excludedFolders():
    folders_and_results = {
        '/var/.git': True,
        '/var/.git/tra/ra': True,
        '/var/tmp/.hg': True,
        '/var/tmp/.hg/git': True,
        '/var/tmp/.bzr': True,
        '/var/tmp/.bzr/git/tra': True,
        '/var/git': False,
        '/var/git/tra/ra': False,
        '23': False,
        '': False,
        'D': False,
        '\\': False,
        '|': False,
        '/': False,
    }

    for (folder, result) in folders_and_results.items():
        assert ignore_folder(folder) == result
