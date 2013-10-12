#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Tests for the capturadio.Recorder class.
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))

import pytest
from fixtures import test_folder


from capturadio import Configuration, Recorder

@pytest.mark.xfail
def test_write_file(test_folder):
    config = Configuration(reset = True, folder=str(test_folder))
    recorder = Recorder()
    folder = test_folder.mkdir('casts')
    file_name = os.path.join(str(folder), 'output.mp3')
    stream_url = 'http://example.org/stream.mp3'
    recorder._write_stream_to_file(stream_url, file_name, 2)
    assert os.path.exists(file_name)

# TODO: Create fixtures for source file, target file, etc.
def test_copy_file_to_destination(test_folder):
    config = Configuration(reset = True, folder=str(test_folder))
    folder = test_folder.mkdir('casts')
    assert test_folder
    config.set_destination(str(folder))
    source_file = folder.join('output.mp3')
    source_file.write('')
    source = str(source_file)
    target = str(test_folder.join('mystation', 'myshow', 'myepisode.pm3'))
    recorder = Recorder()
    recorder._copy_file_to_destination(source, target)
    assert os.path.exists(target)
    assert os.path.isfile(target)
