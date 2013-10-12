#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Tests for the captiradio.Configuration class.
It also contains tests for capturadio.Show and capturadio.Station,
as they are greated and managed with the Configuration class.
"""

import os, sys
import pytest
from pprint import pprint, pformat

sys.path.insert(0, os.path.abspath('.'))

from capturadio import Configuration, Station, Show

@pytest.fixture
def test_folder(request, tmpdir):
  olddir = tmpdir.chdir()
  request.addfinalizer(olddir.chdir)
  tmpdir.join('capturadiorc').write('''
[settings]
destination = {0}/demodata
date_pattern = %d.%m.%Y
comment_pattern:  Show: %show
  Date: %date
  Website: %link_url
  Copyright: %year %station

[stations]
dlf = http://example.org/dlf
dkultur = http://example.org/dkultur
wdr2 = http://example.org/wdr2

[feed]
url = http://my.example.org
title = Internet Radio Recordings
about_url = http://my.example.org/about.html
description = Recordings
language = en
filename = rss.xml
default_logo_url = http://example.org/default.png
default_logo_copyright = A Creative Commons license

[dlf]
name = Deutschlandfunk
link_url = http://example.org/dlf
logo_url = http://example.org/dlf.png
date_pattern = %d.%m.%Y %H:%M

[nachtradio]
title = Nachtradio
duration = 3300
link_url = http://example.org/nachtradio
logo_url = http://example.org/nachtradio.png
station = dlf

[weather]
title = Weather forecast
duration = 300
logo_url = http://example.org/weather.png
station = dlf

[wdr2]
title = WDR 2
link_url = http://example.org/wdr2
logo_url = http://example.org/wdr2.png

[news]
title = Latest news
duration = 300
link_url = http://example.org/wdr2/news
logo_url = http://example.org/wdr2/news.png
station = wdr2
date_pattern = %Y-%m-%d
'''.format(str(tmpdir)))
  return tmpdir

def test_configuration(test_folder):
  config = Configuration(
      reset = True,
      folder = str(test_folder),
      destination = os.path.join(str(test_folder), 'demodata')
  )
  config2 = Configuration()
  assert config.__dict__ == config2.__dict__
  assert config.date_pattern == '%d.%m.%Y'
  assert config.destination == os.path.join(str(test_folder), 'demodata')

  assert len(config.stations) == 3
  for station_id, station in config.stations.items():
      assert isinstance(station, Station)

  assert 'dlf' in config.stations.keys()

  assert config.stations['dlf'].stream_url == 'http://example.org/dlf'
  assert config.stations['dlf'].name == 'Deutschlandfunk'
  assert config.stations['dlf'].logo_url == 'http://example.org/dlf.png'
  assert config.stations['dlf'].link_url == 'http://example.org/dlf'
  assert config.stations['dlf'].date_pattern == '%d.%m.%Y %H:%M'

  assert 'dkultur' in config.stations.keys()
  assert config.stations['dkultur'].stream_url == 'http://example.org/dkultur'
  assert config.stations['dkultur'].name == 'dkultur'
  assert config.stations['dkultur'].logo_url == 'http://example.org/default.png'
  assert config.stations['dkultur'].link_url == 'http://my.example.org/'
  assert not 'date_pattern' in config.stations['dkultur'].__dict__
  assert config.stations['dkultur'].get_date_pattern() == '%d.%m.%Y'

  assert 'wdr2' in config.stations.keys()
  assert config.stations['wdr2'].stream_url == 'http://example.org/wdr2'
  assert config.stations['wdr2'].name == 'wdr2'
  assert config.stations['wdr2'].logo_url == 'http://example.org/wdr2.png'
  assert config.stations['wdr2'].link_url == 'http://example.org/wdr2'
  assert not 'date_pattern' in config.stations['wdr2'].__dict__

  assert len(config.shows) == 3
  for show_id, show in config.shows.items():
      assert isinstance(show, Show)

  assert 'nachtradio' in config.shows.keys()

  show = config.shows['nachtradio']
  assert show.logo_url == 'http://example.org/nachtradio.png'
  assert show.link_url == 'http://example.org/nachtradio'
  assert show.duration == 3300
  assert show.get_date_pattern() == '%d.%m.%Y %H:%M'

  show = config.shows['news']
#  assert show.logo_url == 'http://example.org/nachtradio.png'
#  assert show.link_url == 'http://example.org/nachtradio'
  assert show.duration == 300
  assert show.get_date_pattern() == '%Y-%m-%d'

def test_old_style_configuration(test_folder):
  test_folder.join('capturadiorc.oldstyle').write('''[settings]
destination = {0}/demodata ; path relative to runtime dir
date_pattern = %d.%m.%Y %H:%M

[stations]
dlf = http://example.org/dlf
dkultur = http://example.org/dkultur
wdr2 =  http://example.org/wdr2

; settings for the Podcast feed
[feed]
url = http://my.example.org
title = Internet Radio Recordings
about_url = http://my.example.org/about.html
description = Recordings
language = en
filename = rss.xml
default_logo_url = http://example.org/default.png
default_logo_copyright = A Creative Commons license

; additional settings for station 'dlf'
[dlf]
name = Deutschlandfunk
link_url = http://example.org/dlf
logo_url = http://example.org/dlf.png
shows = nachtradio  weather

; Settings for the show "Nachtradio" on station "dlf"
[nachtradio]
title = Nachtradio
duration = 3300
link_url = http://example.org/nachtradio
logo_url = http://example.org/nachtradio.png

[weather]
title = Weather forecast
duration = 300
logo_url = http://example.org/weather.png

[wdr2]
title = WDR 2
link_url = http://example.org/wdr2
logo_url = http://example.org/wdr2.png
shows = news

[news]
title = Latest news
duration = 300
link_url = http://example.org/wdr2/news
logo_url = http://example.org/wdr2/news.png
'''.format(str(test_folder)))

  test_folder.join('capturadiorc.newstyle').write('''[settings]
destination = {0}/demodata
date_pattern = %d.%m.%Y %H:%M

[stations]
dlf = http://example.org/dlf
dkultur = http://example.org/dkultur
wdr2 = http://example.org/wdr2

[feed]
url = http://my.example.org
title = Internet Radio Recordings
about_url = http://my.example.org/about.html
description = Recordings
language = en
filename = rss.xml
default_logo_url = http://example.org/default.png
default_logo_copyright = A Creative Commons license

[dlf]
name = Deutschlandfunk
link_url = http://example.org/dlf
logo_url = http://example.org/dlf.png

[nachtradio]
title = Nachtradio
duration = 3300
link_url = http://example.org/nachtradio
logo_url = http://example.org/nachtradio.png
station = dlf

[weather]
title = Weather forecast
duration = 300
logo_url = http://example.org/weather.png
station = dlf

[wdr2]
title = WDR 2
link_url = http://example.org/wdr2
logo_url = http://example.org/wdr2.png

[news]
title = Latest news
duration = 300
link_url = http://example.org/wdr2/news
logo_url = http://example.org/wdr2/news.png
station = wdr2

'''.format(str(test_folder)))

  config = Configuration(
      folder = str(test_folder),
      filename = 'capturadiorc.oldstyle',
      reset=True
  )
  assert config.filename == os.path.join(config.folder, 'capturadiorc.oldstyle')
  import filecmp
  assert filecmp.cmp(
      os.path.join(config.folder, 'capturadiorc.oldstyle.new'),
      os.path.join(config.folder, 'capturadiorc.newstyle')
  )

def test_change_destination(test_folder):
  config = Configuration(reset=True, folder=str(test_folder))
  new_folder = str(test_folder.mkdir('destination'))
  config.set_destination(new_folder)
  assert config.destination == new_folder

def test_station_ids(test_folder):
  config = Configuration(reset=True, folder=str(test_folder))
  assert ['dkultur', 'dlf', 'wdr2'] == config.get_station_ids()

def test_add_station(test_folder):
  config = Configuration(reset=True, folder=str(test_folder))
  config.add_station('me', 'http://example.org/stream', 'Me', 'http://example.org/logo.png')
  assert ['me', 'dkultur', 'dlf', 'wdr2'] == config.get_station_ids()

  station = config.stations['me']
  assert isinstance(station, Station)
  assert station.name == 'Me'
  assert station.id   == 'me'
  assert station.logo_url == 'http://example.org/logo.png'
  assert station.stream_url == 'http://example.org/stream'
  assert station.shows == []

def test_add_show_to_station(test_folder):
  config = Configuration(reset=True, folder=str(test_folder))
  station = config.stations['dlf']
  show = config.add_show(station, 'news', 'Latest News', 10)
  assert isinstance(show, Show)

  assert len(config.shows) == 3
  for show_id, show in config.shows.items():
      assert isinstance(show, Show)
  assert config.shows['news'].name == 'Latest News'
  assert config.shows['news'].logo_url == None
  assert config.shows['news'].station == station
  assert config.shows['news'].duration == 10

def test_parse_duration():
  from capturadio.util import parse_duration

  assert parse_duration("10h") == 36000
  assert parse_duration("50m") == 3000
  assert parse_duration("300s") == 300
  assert parse_duration("300") == 300
  assert parse_duration("1h15m20") == 4520

  assert parse_duration("-50m") == 0
  assert parse_duration("-300s") == 0
  assert parse_duration("-300") == 0
  assert parse_duration("1h-15m20") == 3600
  assert parse_duration("trara") == 0
  assert parse_duration("12trara") == 12

def test_excluded_folders():
  excluded_folders = [
      '/var/.git',
      '/var/.git/tra/ra',
      '/var/tmp/.hg',
      '/var/tmp/.hg/git',
      '/var/tmp/.bzr',
      '/var/tmp/.bzr/git/tra',
      ]
  included_folders = [
      '/var/git',
      '/var/git/tra/ra',
      ]

  from create_podcast_feed import excluded_folder

  for folder in excluded_folders:
    assert excluded_folder(folder) == True
  for folder in included_folders:
    assert excluded_folder(folder) == False
