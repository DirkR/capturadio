#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Tests for the capturadio.Recorder class.
"""

import sys
import os
import time
import pytest
from fixtures import test_folder, config
sys.path.insert(0, os.path.abspath('.'))

from capturadio import Recorder, Show


def test_write_file(test_folder, config, monkeypatch):
    def mockreturn(path):
        return open(os.path.join(os.path.dirname(__file__), 'testfile.mp3'), 'r')
    import capturadio
    monkeypatch.setattr(capturadio, 'urlopen', mockreturn)

    recorder = Recorder()
    recorder.start_time = time.time()

    folder = test_folder.mkdir('casts')
    file_name = os.path.join(str(folder), 'output.mp3')
    stream_url = 'http://example.org/stream.mp3'
    recorder._write_stream_to_file(stream_url, file_name, 2)
    assert os.path.exists(file_name)


# TODO: Create fixtures for source file, target file, etc.
def test_copy_file_to_destination(config, test_folder):
    source_file = test_folder.join('output.mp3')
    source_file.write('')
    source = str(source_file)
    target = str(test_folder.join('mystation', 'myshow', 'myepisode.pm3'))
    recorder = Recorder()
    recorder._copy_file_to_destination(source, target)
    assert os.path.exists(target)
    assert os.path.isfile(target)


def test_add_metadata(config, test_folder):
    import time
    media_file = test_folder.join('mystation', 'myshow', 'myepisode.pm3')
    station = config.stations['dlf']
    show = Show(station, 'me', 'Me', 2)
    recorder = Recorder()
    recorder.start_time = time.time()
    recorder._copy_file_to_destination(os.path.join(os.path.dirname(__file__), 'testfile.mp3'), str(media_file))
    recorder._add_metadata(show, str(media_file))
    try:
        # Python 2.x
        from mutagen.mp3 import MP3
    except ImportError:
        # Python 3.x
        from mutagenx.mp3 import MP3

    audio = MP3(str(media_file))
    #assert 'tit' == audio['TIT2'].text[0]
    assert 'Podcast' == audio['TCON'].text[0]
    assert 'Deutschlandfunk' == audio['TPE1'].text[0]
    assert 'Deutschlandfunk' == audio['TCOP'].text[0]
    assert 'Me' == audio['TALB'].text[0]
    assert 'http://example.org/dlf' == audio['TCOM'].text[0]
    assert u'2000' == audio['TLEN'].text[0]
