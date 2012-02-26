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

		print config.shows

		self.assertEqual(len(config.shows), 1)
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

		self.assertEqual(len(config.shows), 2)
		for show_id, show in config.shows.items():
			self.assertTrue(isinstance(show, Show))
		self.assertEqual(config.shows['dlf_news'].name, 'Latest News')
		self.assertEqual(config.shows['dlf_news'].logo_url, None)
		self.assertEqual(config.shows['dlf_news'].station, station)
		self.assertEqual(config.shows['dlf_news'].duration, 10)

	def testFindStationByName(self):
		config = Configuration()
		station = config.find_station_by_name('Deutschlandfunk')
		self.assertTrue(isinstance(station, Station))
		self.assertEqual(station.stream_url, 'http://example.org/dlf')
		self.assertEqual(station.name, 'Deutschlandfunk')
		self.assertEqual(station.logo_url, 'http://example.org/dlf.png')


	def testLogoFinder(self):
		config = Configuration()
		station = config.stations['dlf']
		config.add_show(station, 'news', 'Latest News', 10)
		self.assertEqual(config.find_showlogo_by_id('dlf_news'), 'http://example.org/dlf.png')

		station = config.stations['dkultur']
		config.add_show(station, 'news', 'Latest News', 10)
		self.assertEqual(config.find_showlogo_by_id('dkultur_news'), 'http://example.org/default.png')

		config.add_show(station, 'news2', 'Latest News', 20, 'http://example.org/news.png')
		self.assertEqual(config.find_showlogo_by_id('dkultur_news2'), 'http://example.org/news.png')

	def testFindShow(self):
		pass

		
#	def assertSpec(self, condition, message):
#		...

#from capturadio import Recorder
#recorder = Recorder()
#recorder.capture()

if __name__ == "__main__":
	unittest.main()
