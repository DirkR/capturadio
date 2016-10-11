#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Tests for the capturadio.Recorder class.
"""

import sys
import os
import time
import codecs
import pytest
from fixtures import test_folder, config
sys.path.insert(0, os.path.abspath('.'))

from capturadio.entities import Show, Episode
from capturadio.recorder import Recorder


def test_write_file(test_folder, config, monkeypatch):
    def mockreturn(path):
        filename = os.path.join(os.path.dirname(__file__), 'testfile.mp3')
        return open(filename, 'rb')
    import capturadio.recorder
    monkeypatch.setattr(capturadio.recorder, 'urlopen', mockreturn)

    folder = test_folder.mkdir('casts')
    show = config.shows['weather']
    episode = capturadio.Episode(config, show)
    episode.filename = os.path.join(str(folder), 'output.mp3')
    episode.duration = 3

    recorder = Recorder()
    recorder._write_stream_to_file(episode)
    assert os.path.exists(episode.filename)


def test_add_metadata(config, test_folder):
    import shutil
    from mutagenx.mp3 import MP3

    media_file = test_folder.join('mystation', 'myshow', 'myepisode.pm3')
    os.makedirs(os.path.dirname(str(media_file)))
    shutil.copy(os.path.join(os.path.dirname(__file__), 'testfile.mp3'), str(media_file))

    station = config.stations['dlf']
    show = Show(config, station, 'me', 'Me', 2)
    episode = Episode(config, show)
    episode.filename = str(media_file)
    recorder = Recorder()
    recorder._add_metadata(episode)

    audio = MP3(str(media_file))
    #assert 'tit' == audio['TIT2'].text[0]
    assert 'Podcast' == audio['TCON'].text[0]
    assert 'Deutschlandfunk' == audio['TPE1'].text[0]
    assert 'Deutschlandfunk' == audio['TCOP'].text[0]
    assert 'Me' == audio['TALB'].text[0]
    assert 'http://example.org/dlf' == audio['TCOM'].text[0]
    assert u'2000' == audio['TLEN'].text[0]
