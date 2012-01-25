#!/usr/bin/env python2.7
# This script traverses a directory tree and creates a rss file in the root folder
# containing all found mp3 files as items
# Original found at
# Found at http://snippsnapp.polite.se/wiki?action=browse&diff=0&id=PyPodcastGen
# and adopted for my needs

import datetime, urlparse, urllib, string, os
import PyRSS2Gen
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

class Audiofile:
    def __init__(self, collection, basename):
        self.basename = string.replace(basename, collection.dirname, '', 1)
        if (os.path.isabs(self.basename)):
            self.basename = string.replace(self.basename, '/', '', 1)
        self.path = os.path.join(collection.dirname, basename)
        self.link = urlparse.urljoin(collection.urlbase, urllib.quote(self.basename))

        audio = MP3(self.path, ID3=EasyID3)

        try:
            title = audio['title'][0]
            if title:
                self.title = title
            else:
                self.title = basename[:-4]

            self.description = string.replace(basename[:-4], collection.dirname, '')
            if (self.description.startswith('/')):
                self.description = self.description[1:]
                self.description = string.replace(self.description, '/', ' &raquo; ')

            self.playtime = audio.info.length
        except Exception, e:
            print "Skipped metadata for %s, because an exception was thrown: %s" % (self.basename, e)
            self.title = basename[:-4]
            self.description = basename[:-4]
            self.playtime = 0

        self.guid = PyRSS2Gen.Guid(self.link)
        self.size = os.path.getsize(self.path)
        self.enclosure = PyRSS2Gen.Enclosure(self.link, self.playtime, "audio/mpeg")
        self.pubdate = datetime.datetime.fromtimestamp(os.path.getmtime(self.path))
                              

class Audiofiles:
    """
    A collection of audiofiles and some metadata, used as the basis for at 
    
    """

    def __init__(self,urlbase,title, link, description, language):


        self.urlbase = urlbase
        self.title = title
        self.link = link
        self.description = description
        self.language = language
        
        self.data = []

        self.generator = PyRSS2Gen._generator_name        

    def append(self,audiofile):
        self.data.append(audiofile)

    def readfolder(self,dirname):
        self.dirname = dirname
        for dirname, dirnames, filenames in os.walk(dirname):
            for filename in filenames:
                path = os.path.join(dirname,filename)
                if os.path.exists(path) and os.path.isfile(path) and path.endswith(".mp3"):
                    if (path.startswith('./')):
                        path = string.replace(path, './', '', 1)
                    audiofile = Audiofile(self, path)
                    self.append(audiofile)

    def rssitems(self,n=10):
        result = []
        for audiofile in self.data:

            rssitem = PyRSS2Gen.RSSItem(
                title = audiofile.title,
                link = audiofile.link,
                description = audiofile.description,
                guid = audiofile.guid,
                pubDate = audiofile.pubdate,
                enclosure = audiofile.enclosure
            )
            result.append(rssitem)

        waste = [(i.pubDate,i) for i in result]
        waste.sort()
        waste.reverse()
        waste = waste[:n]
        result = [pair[1] for pair in waste]
        
        return result

    def getrss(self):
        return PyRSS2Gen.RSS2(title = self.title,
                              link = self.link,
                              description = self.description,
                              language = self.language,
                              generator = self.generator,
                              lastBuildDate = datetime.datetime.now(),                         
                              items = self.rssitems())
        
def process_folder(path, root_path):
    import ConfigParser

    local_path = string.replace(path, root_path, '')
    if (local_path != ''):
        if (local_path.startswith('/')):
            local_path = local_path[1:]
        if (not local_path.endswith('/')):
            local_path += '/'

    if (config.has_section('feed')):
        feed_title = config.get('feed', 'title', 'Internet radio recordings')
        feed_url = config.get('feed', 'url', 'http://example.org')
        if (not feed_url.endswith('/')):
            feed_url += "/"
        feed_description = config.get('feed', 'description', 'Recordings of internet radio station broadcastings')
        feed_about_url = config.get('feed', 'about_url',  feed_url + '/about')
        feed_language = config.get('feed', 'language',  'en')
    else:
        feed_title = 'Internet radio recordings'
        feed_url = 'http://example.org/'
        feed_description = 'Recordings of internet radio station broadcastings'
        feed_about_url = feed_url + 'about'
        feed_language = 'en'

    if (local_path != ''):
        feed_title += " - " + string.replace(local_path, '/', ' - ')

    audiofiles = Audiofiles(feed_url + urllib.quote(local_path),
                            feed_title,
                            feed_about_url,
                            feed_description,
                            feed_language)
    audiofiles.readfolder(path)

    if (config.has_section('feed')):
        rss_file = config.get('feed', 'filename',  'rss.xml')
    else:
        rss_file = 'rss.xml'

    rss = audiofiles.getrss()
    rss.write_xml(open(os.path.join(path, rss_file), "w"))


if __name__ == "__main__":
    import argparse
    import ConfigParser


    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('~/.capturadio/capturadiorc'), os.path.expanduser('~/.capturadiorc')])

    parser = argparse.ArgumentParser(description='Generate a rss file containing all mp3 files in this directory and all sub directories.')
    parser.add_argument('-r', action='store_true', help="Put an rss file into every subfolder, that contains all episodes in all of it's subfolders.")
    parser.add_argument('directory', nargs='?', help='The directory to be indexed. Use current directory if ommitted.')
    args = parser.parse_args()


    if (args.directory != None and os.path.exists(args.directory) and os.path.isdir(args.directory)):
        path = args.directory
        if (path.startswith('./')):
            path = string.replace(path, './', '', 1)
        if (not os.path.isabs(path)):
            path = os.path.join(os.getcwd(), path)
        print "use path from cmdline: %s" % path
    elif(config.has_section('settings') and config.has_option('settings', 'destination')):
        path = os.path.expanduser(config.get('settings', 'destination'))
        print "use path from configuration: %s" % path
    else:
        path = os.getcwd()
        print "use path from defaults (pwd): %s" % path

    if (not args.r):
        process_folder(path, path)
    else:
        for dirname, dirnames, filenames in os.walk(path):
            process_folder(dirname, path)
