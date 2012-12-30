#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import unittest, os, sys

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('..'))

from capturadio import Configuration, Station, Show

class ConfigurationTestCase(unittest.TestCase):
    test_folder = os.path.join(os.path.dirname(__file__), 'demodata')

    def setUp(self):
        Configuration.configuration_folder = os.path.dirname(__file__)
        Configuration._shared_state = {}

        if (os.path.exists(ConfigurationTestCase.test_folder)):
            os.removedirs(ConfigurationTestCase.test_folder)
        os.mkdir(ConfigurationTestCase.test_folder, 0755)

    def tearDown(self):
        os.removedirs(ConfigurationTestCase.test_folder)

    def testConfiguration(self):
        config = Configuration()

        self.assertEqual(config.date_pattern, '%d.%m.%Y')
        self.assertEqual(config.destination, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demodata'))

        self.assertEqual(len(config.stations), 3)
        for station_id, station in config.stations.items():
            self.assertTrue(isinstance(station, Station))

        self.assertTrue('dlf' in config.stations.keys())

        self.assertEqual(config.stations['dlf'].stream_url, 'http://example.org/dlf')
        self.assertEqual(config.stations['dlf'].name, 'Deutschlandfunk')
        self.assertEqual(config.stations['dlf'].logo_url, 'http://example.org/dlf.png')
        self.assertEqual(config.stations['dlf'].link_url, 'http://example.org/dlf')
        self.assertEqual(config.stations['dlf'].date_pattern, '%d.%m.%Y %H:%M')

        self.assertTrue('dkultur' in config.stations.keys())
        self.assertEqual(config.stations['dkultur'].stream_url, 'http://example.org/dkultur')
        self.assertEqual(config.stations['dkultur'].name, 'dkultur')
        self.assertEqual(config.stations['dkultur'].logo_url, 'http://example.org/default.png')
        self.assertEqual(config.stations['dkultur'].link_url, 'http://my.example.org/')
        self.assertFalse('date_pattern' in config.stations['dkultur'].__dict__)
        self.assertEqual(config.stations['dkultur'].get_date_pattern(), '%d.%m.%Y')

        self.assertTrue('wdr2' in config.stations.keys())
        self.assertEqual(config.stations['wdr2'].stream_url, 'http://example.org/wdr2')
        self.assertEqual(config.stations['wdr2'].name, 'wdr2')
        self.assertEqual(config.stations['wdr2'].logo_url, 'http://example.org/wdr2.png')
        self.assertEqual(config.stations['wdr2'].link_url, 'http://example.org/wdr2')
        self.assertFalse('date_pattern' in config.stations['wdr2'].__dict__)

        self.assertEqual(len(config.shows), 3)
        for show_id, show in config.shows.items():
            self.assertTrue(isinstance(show, Show))

        self.assertTrue('nachtradio' in config.shows.keys())

        show = config.shows['nachtradio']
        self.assertEqual(show.logo_url, 'http://example.org/nachtradio.png')
        self.assertEqual(show.link_url, 'http://example.org/nachtradio')
        self.assertEqual(show.duration, 3300)
        self.assertEqual(show.get_date_pattern(), '%d.%m.%Y %H:%M')

        show = config.shows['news']
#        self.assertEqual(show.logo_url, 'http://example.org/nachtradio.png')
#        self.assertEqual(show.link_url, 'http://example.org/nachtradio')
        self.assertEqual(show.duration, 300)
        self.assertEqual(show.get_date_pattern(), '%Y-%m-%d')


    def testOldStyleConfiguration(self):
        Configuration.filename = 'capturadiorc.oldstyle'
        Configuration._shared_state = {}
        config = Configuration()

        import filecmp

        self.assertTrue(filecmp.cmp(
            os.path.join(Configuration.configuration_folder, 'capturadiorc.oldstyle.new'),
            os.path.join(Configuration.configuration_folder, 'capturadiorc.newstyle')
        ))


    def testAddShowToStation(self):
        config = Configuration()
        station = config.stations['dlf']
        show = config.add_show(station, 'news', 'Latest News', 10)
        self.assertTrue(isinstance(show, Show))

        self.assertEqual(len(config.shows), 3)
        for show_id, show in config.shows.items():
            self.assertTrue(isinstance(show, Show))
        self.assertEqual(config.shows['news'].name, 'Latest News')
        self.assertEqual(config.shows['news'].logo_url, None)
        self.assertEqual(config.shows['news'].station, station)
        self.assertEqual(config.shows['news'].duration, 10)

    def testParseDuration(self):
        from capturadio.util import parse_duration

        self.assertEqual(parse_duration("10h"), 36000)
        self.assertEqual(parse_duration("50m"), 3000)
        self.assertEqual(parse_duration("300s"), 300)
        self.assertEqual(parse_duration("300"), 300)
        self.assertEqual(parse_duration("1h15m20"), 4520)

        self.assertEqual(parse_duration("-50m"), 0)
        self.assertEqual(parse_duration("-300s"), 0)
        self.assertEqual(parse_duration("-300"), 0)
        self.assertEqual(parse_duration("1h-15m20"), 3600)
        self.assertEqual(parse_duration("trara"), 0)
        self.assertEqual(parse_duration("12trara"), 12)


class ExcludedFoldersTest(unittest.TestCase):
    def testExcludedFolders(self):
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
            self.assertEqual(excluded_folder(folder), True)
        for folder in included_folders:
            self.assertEqual(excluded_folder(folder), False)

if __name__ == "__main__":
    unittest.main()
