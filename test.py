#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import unittest
import os, sys
from capturadio import Configuration, Station, Show

class ConfigurationTestCase(unittest.TestCase):

	def setUp(self):
		Configuration.filename = "./test.capturadiorc"
		pass

	def tearDown(self):
		pass

	def testConfiguration(self):
		config = Configuration()

		self.assertEqual(config.date_pattern, '%Y-%m-%d %H:%M')
		self.assertEqual(config.destination, os.getcwd())

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


	def testAddShowToStation(self):
		config = Configuration()
		station = config.stations['dlf']
		config.add_show(station, 'news', 'Latest News')

		self.assertEqual(len(config.shows), 1)
		for show_id, show in config.shows.items():
			self.assertTrue(isinstance(show, Show))
		self.assertEqual(config.shows['news'].name, 'Latest News')
		self.assertEqual(config.shows['news'].logo_url, None)

	def testlogoFinder(self):
		config = Configuration()
		station = config.stations['dlf']
		config.add_show(station, 'dlf_news', 'Latest News')
		self.assertEqual(config.find_showlogo_by_id('dlf_news'), 'http://example.org/dlf.png')

		station = config.stations['dkultur']
		config.add_show(station, 'dkultur_news', 'Latest News')
		self.assertEqual(config.find_showlogo_by_id('dkultur_news'), 'http://example.org/default.png')

		config.add_show(station, 'dkultur_news2', 'Latest News', 'http://example.org/news.png')
		self.assertEqual(config.find_showlogo_by_id('dkultur_news2'), 'http://example.org/news.png')


		
#	def assertSpec(self, condition, message):
#		...

#from capturadio import Recorder
#recorder = Recorder()
#recorder.capture()

if __name__ == "__main__":
	unittest.main()
