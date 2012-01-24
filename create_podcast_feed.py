#/usr/bin/python2.7
# This script traverses a directory tree and creates a rss file in the root folder
# containing all found mp3 files as items
# Original found at
# Found at http://snippsnapp.polite.se/wiki?action=browse&diff=0&id=PyPodcastGen
# and adopted for my needs

import datetime,urlparse,os
import PyRSS2Gen
import eyeD3
import string

class Audiofile:
    def __init__(self, collection, basename):
        self.basename = string.replace(basename, collection.dirname, '', 1)
        if (os.path.isabs(self.basename)):
            self.basename = string.replace(self.basename, '/', '', 1)
        self.path = os.path.join(collection.dirname, basename)
        self.link = urlparse.urljoin(collection.urlbase, self.basename)

        tag = eyeD3.Tag()
        tag.link(self.path)

        try:
            mp3file = eyeD3.Mp3AudioFile(self.path)

            title = tag.getTitle()
            if title:
                self.title = title
            else:
                self.title = basename[:-4]

            description = tag.getComment()
            if description:
                self.description = description
            else:
                self.description = basename[:-4]

            self.playtime = mp3file.getPlayTimeString()
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
        print "Read folder: %s" % (dirname)
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
        
        

if __name__ == "__main__":
    #Example usage
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Generate a rss file containing all mp3 files in this directory and all sub directories.')
    parser.add_argument('-r', metavar='', help="Put an rss file into every subfolder, that contains all episodes in all of it's subfolders.")
    parser.add_argument('directory', help='The directory to be indexed. Use current directory if ommitted.')
    args = parser.parse_args()

    path = os.getcwd()
    if (args.directory != None):
        if os.path.exists(args.directory) and os.path.isdir(args.directory):
            path = args.directory
            if (path.startswith('./')):
                path = string.replace(path, './', '', 1)
            if (not os.path.isabs(path)):
                path = os.path.join(os.getcwd(), path)

    audiofiles = Audiofiles("http://music.niebegeg.net",
                            "Mitschnitte",
                            "http://music.niebegeg.net/aboutyourpodcast",
                            "Recordings of internet radio station broadcastings",
                            "en")

    audiofiles.readfolder(path)
    outfilename = os.path.join(path, "rss.xml")

    rss = audiofiles.getrss()
    rss.write_xml(open(outfilename, "w"))