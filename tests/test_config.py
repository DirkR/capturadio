#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Tests for the capturadio.Configuration class.
It also contains tests for capturadio.Show and capturadio.Station,
as they are greated and managed with the Configuration class.
"""

import os
import sys
from fixtures import test_folder, config

sys.path.insert(0, os.path.abspath('.'))

from capturadio import Configuration, Station, Show


def test_configuration(test_folder):
    config = Configuration(
        reset=True,
        folder=str(test_folder),
        destination=os.path.join(str(test_folder), 'demodata')
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
    assert config.stations['dkultur'].link_url == 'http://my.example.org'
    assert config.stations['dkultur'].date_pattern == '%d.%m.%Y'

    assert 'wdr2' in config.stations.keys()
    assert config.stations['wdr2'].stream_url == 'http://example.org/wdr2'
    assert config.stations['wdr2'].name == 'wdr2'
    assert config.stations['wdr2'].logo_url == 'http://example.org/wdr2.png'
    assert config.stations['wdr2'].link_url == 'http://example.org/wdr2'
    assert config.stations['wdr2'].date_pattern == '%d.%m.%Y'

    assert len(config.shows) == 3
    for show_id, show in config.shows.items():
        assert isinstance(show, Show)

    assert 'nachtradio' in config.shows.keys()

    show = config.shows['nachtradio']
    assert show.logo_url == 'http://example.org/nachtradio.png'
    assert show.link_url == 'http://example.org/nachtradio'
    assert show.duration == 3300
    assert show.date_pattern == '%d.%m.%Y %H:%M'

    show = config.shows['news']
    #  assert show.logo_url == 'http://example.org/nachtradio.png'
    #  assert show.link_url == 'http://example.org/nachtradio'
    assert show.duration == 300
    assert show.date_pattern == '%Y-%m-%d'


def test_old_style_configuration(test_folder):
    test_folder.join('capturadiorc.oldstyle').write('''[settings]
destination = {0}/demodata
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
title = Internet Radio Recordings
about_url = http://my.example.org/about.html
description = Recordings
language = en
filename = rss.xml
default_logo_url = http://example.org/default.png
default_logo_copyright = A Creative Commons license
base_url = http://my.example.org

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

    configuration = Configuration(
        folder=str(test_folder),
        filename='capturadiorc.oldstyle',
        reset=True
    )
    assert configuration.filename == os.path.join(
        configuration.folder,
        'capturadiorc.oldstyle'
    )
    assert Configuration.changed_settings is True
    assert os.path.exists(configuration.filename)
    assert os.path.exists(configuration.filename + '.bak')
    import filecmp
    assert filecmp.cmp(
        os.path.join(configuration.folder, 'capturadiorc.oldstyle'),
        os.path.join(configuration.folder, 'capturadiorc.newstyle')
    )


def test_change_destination(test_folder):
    config = Configuration(reset=True, folder=str(test_folder))
    new_folder = str(test_folder.mkdir('destination'))
    config.set_destination(new_folder)
    assert config.destination == new_folder


def test_station_ids(test_folder):
    config = Configuration(reset=True, folder=str(test_folder))
    assert ['dkultur', 'dlf', 'wdr2'].sort() == list(config.get_station_ids()).sort()


def test_add_station(test_folder):
    configuration = Configuration(reset=True, folder=str(test_folder))
    assert configuration.folder == test_folder
    station = configuration.add_station('me', 'http://example.org/stream', 'Me')
    assert ['me', 'dkultur', 'dlf', 'wdr2'].sort() == configuration.get_station_ids().sort()

    station = configuration.stations['me']
    assert isinstance(station, Station)
    assert station.name == 'Me'
    assert station.id == 'me'
    assert station.logo_url == 'http://example.org/default.png'
    assert station.stream_url == 'http://example.org/stream'
    assert station.shows == []


def test_add_show_to_station(test_folder):
    config = Configuration(reset=True, folder=str(test_folder))
    station = config.stations['dlf']
    show = config.add_show(config, station, 'news', 'Latest News', 10)
    assert isinstance(show, Show)

    assert len(config.shows) == 3
    for show_id, show in config.shows.items():
        assert isinstance(show, Show)
    assert config.shows['news'].name == 'Latest News'
    assert config.shows['news'].logo_url == 'http://example.org/dlf.png'
    assert config.shows['news'].station == station
    assert config.shows['news'].duration == 10


def test_parse_duration():
    from capturadio.util import parse_duration

    assert parse_duration("10h") == 36000
    assert parse_duration("50m") == 3000
    assert parse_duration("300s") == 300
    assert parse_duration("300") == 300
    assert parse_duration("1h15m20") == 4520
    assert parse_duration("5d2h") == 439200
    assert parse_duration("5d20s") == 432020

    assert parse_duration("-50m") == 0
    assert parse_duration("-300s") == 0
    assert parse_duration("-300") == 0
    assert parse_duration("1h-15m20") == 3600
    assert parse_duration("trara") == 0
    assert parse_duration("12trara") == 12
