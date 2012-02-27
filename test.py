#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import unittest
import os, sys
from capturadio import Configuration, Station, Show

class ConfigurationTestCase(unittest.TestCase):

	def setUp(self):
		Configuration.filename = "./test.capturadiorc"

	def tearDown(self):
		pass

	def testConfiguration(self):
		config = Configuration()

		self.assertEqual(config.date_pattern, '%d.%m.%Y %H:%M')
		self.assertEqual(config.destination, './demodata')

		self.assertEqual(len(config.stations), 2)
		for station_id, station in config.stations.items():
			self.assertTrue(isinstance(station, Station))

		self.assertTrue('dlf' in config.stations.keys())

		self.assertEqual(config.stations['dlf'].stream_url, 'http://example.org/dlf')
		self.assertEqual(config.stations['dlf'].name, 'Deutschlandfunk')
		self.assertEqual(config.stations['dlf'].logo_url, 'http://example.org/dlf.png')

		self.assertEqual(config.stations['dkultur'].stream_url,'http://example.org/dkultur')
		self.assertEqual(config.stations['dkultur'].name, 'dkultur')
		self.assertEqual(config.stations['dkultur'].logo_url, 'http://example.org/default.png')

		self.assertEqual(config.stations['dkultur'].stream_url,'http://example.org/dkultur')
		self.assertEqual(config.stations['dkultur'].name, 'dkultur')
		self.assertEqual(config.stations['dkultur'].logo_url, 'http://example.org/default.png')

		self.assertEqual(len(config.shows), 2)
		for show_id, show in config.shows.items():
			self.assertTrue(isinstance(show, Show))

		self.assertTrue('dlf_nachtradio' in config.shows.keys())

		show = config.shows['dlf_nachtradio']
		self.assertEqual(show.logo_url, 'http://example.org/nachtradio.png')
		self.assertEqual(show.duration, 3300)

	def testAddShowToStation(self):
		config = Configuration()
		station = config.stations['dlf']
		show = config.add_show(station, 'news', 'Latest News', 10)
		self.assertTrue(isinstance(show, Show))

		self.assertEqual(len(config.shows), 3)
		for show_id, show in config.shows.items():
			self.assertTrue(isinstance(show, Show))
		self.assertEqual(config.shows['dlf_news'].name, 'Latest News')
		self.assertEqual(config.shows['dlf_news'].logo_url, None)
		self.assertEqual(config.shows['dlf_news'].station, station)
		self.assertEqual(config.shows['dlf_news'].duration, 10)

	def testParseDuration(self):
		from capturadio import parse_duration
		self.assertEqual(parse_duration("10h"),     36000)
		self.assertEqual(parse_duration("50m"),     3000)
		self.assertEqual(parse_duration("300s"),    300)
		self.assertEqual(parse_duration("300"),     300)
		self.assertEqual(parse_duration("1h15m20"), 4520)

		self.assertEqual(parse_duration("-50m"),     0)
		self.assertEqual(parse_duration("-300s"),    0)
		self.assertEqual(parse_duration("-300"),     0)
		self.assertEqual(parse_duration("1h-15m20"), 3600)
		self.assertEqual(parse_duration("trara"),    0)
		self.assertEqual(parse_duration("12trara"),  12)

if __name__ == "__main__":
	unittest.main()
