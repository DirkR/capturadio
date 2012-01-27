# CaptuRadio

by Dirk Ruediger <<dirk@niebegeg.net>>

## Introduction

_CaptuRadio_ is a too to record shows from internet radio stations t your computer or server.
It is written in Python and primary made to run on a server.
_CaptuRadio_ has only been tested on unix-like OSes, like Mac S and Linux.

## Installation

_CaptuRadio_ needs python 2.7 and an unix-like operation system running on your machine.

### Prerequisites

The following python libraries need to be installed beside Python 2.7 to run CapturRadio:

* mutagen -- a Python module to handle audio metadata      
  http://code.google.com/p/mutagen/, tested with version 1.20
* PyRSS2Gen -- a Python library for manipulating RSS feeds   
  http://www.dalkescientific.com/Python/PyRSS2Gen.html, version 1.0.0 and above

### Installation

Simply put the capturadio.py script anywhere on your host. 
To uninstall it you only need to remove it from your disk.

## Usage

_CaptuRadio_ needs some information on the commandline to operate correctly.

    usage: capturadio.py [-h] -l length -s station -b broadcast [-t title]
                     [-d destination]
    
    Capture internet radio programs broadcasted in mp3 encoding format.
    
    optional arguments:
      -h, --help      show this help message and exit
      -l length       Length of recording in seconds
      -s station      Name of the station, defined in 
                      ~/.capturadio/capturadiorc.
      -b broadcast    Title of the broadcast
      -t title        Title of the recording
      -d destination  Destination directory

    Here is a list of defined radio stations: ['list', 'of', 'defined', 'stations']

The option `-l length` tells _CaptuRadio_ how many seconds the capturing should last.

The option `-s station` tells _CaptuRadio_ which station should be accessed. The station name has to be defined in `~/.capturadio/capturadiorc` (see section `Configuration`)below).

The options `-b show` defines the name of the show and  `-t title` optionally defines the name of the episode. This way you can a show that is broadcasted every night, but has another topic very day of the week. If you omit the option `-t`, then _CaptuRadio_ uses the show name as name of the episode.

The option `-d destination` defines location on the disk where captured mp3 tracks (the episodes) will be stored.  _CaptuRadio_ creates sub folders for ever station and show. The resulting mp3 file has the location `station_name/show_name/episode_name-datestring.mp3` inside the destination folder.

## Configuration

At startup _CaptuRadio_ reads all configuration data from `~/.capturadio/capturadiorc`. If this file does not exist, then you have to create it. _CaptuRadio_ comes with a sample configuration file as template.

The station is defined in `~/.capturadio/capturadiorc` in 
the section `[]stations]`. Every entry consists of a key-value-pair
defining the station name and the MP3 stream URL.

    [stations]
    station1 = http://example.org/station1/mp3
    station2 = http://example.net/live/station2
    ...

For every station you can provide an own section in the configuration file. 
There you can define a name of descriptive the station and the URL 
of the station logo.  If the name is defined, then it is used in the mp3
metadata (ID3) and for folder names when storing the file (see notes
above). The logo will be downloaded and embedded into the mp3 file.

    [station1]
    name = My favorite music radio station
    logo = http://example.net/media/images/logo_256.png

## Usage

To capture a mp3 stream you have to define the station (aka the nickname of the stream and the stream URL, see abowe) in `~/.capturadio/capturadiorc`. Now you can run the capturing

    capturadio.py -l 3300 -s station1 -b "My favorite radio show" -t "Monday talk"

The mp3 file will be stored inside the current working directory. You can also put the file somewhere else:

    capturadio.py -l 3300 -s station1 -b "My favorite radio show" -d /var/www/radio

Usually these commands are run by the cron facility on your host.

The command

    capturadio.py -h

provide help as well as a list of all defined stations.

## Downloads

Git clone _CaptuRadio_ from GitHub at https://github.com/DirkR/capturadio

## License

The _CaptuRadio_ code is distributed under GNU GPL license.

## Version History

#### Version 0.6 -- 2012-01-25

* create_podcast_feed.py also uses the configuration file, there's a section `[feed]` provides information for the RSS file.
* MP3 files now contain the timestamp in their filename
* some small fixes

#### Version 0.5 -- 2012-01-24

Initial release.
