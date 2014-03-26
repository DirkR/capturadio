# CaptuRadio

by Dirk Ruediger <<dirk@niebegeg.net>>

## Introduction

_CaptuRadio_ is a tool to record shows from internet radio stations
to your computer or server.  It is written in Python and primary
made to run on a server.
_CaptuRadio_ has only been tested on unix-like OSes, like MacOSX and Linux.


### Prerequisites

_CaptuRadio_ needs python 2.7 and an unix-like operation system running on your machine.
The following python libraries need to be installed beside Python 2.7 to run CapturRadio:

* mutagen -- a Python module to handle audio metadata
  http://code.google.com/p/mutagen/, tested with version 1.21
* PyRSS2Gen -- a Python library for manipulating RSS feeds
  http://www.dalkescientific.com/Python/PyRSS2Gen.html, version 1.1.0 and above
* docopt -- a Python module to handle arguments parsing of cli
  applications, version 0.6 and above

### Installation

Install the application by running the setup script:

    python setup.py install

The app needs a configuration file. Simply run

    recorder.py config setup

and it will create a configuration at `~/.capturadio/capturadiorc`.
You should edit the file and customize it. Especially the destination folder
and the base_url should be adopted.

Run the command

    recorder.py config list

to see the current configuration.

## Usage

_CaptuRadio_ needs some information on the commandline to operate correctly.

    recorder.py show capture <show>

records a pre-defined radio show.
The option `show` tells _CaptuRadio_ which station should be recorded. The show name has
to be defined in `~/.capturadio/capturadiorc` (see section `Configuration` below).

    recorder.py config list

This command lists all defined confuration values.

    recorder.py feed update

By running this command the files providing the RSS feeds are
regenerated.

See `recorder.py help <command>` for more information on a specific command.

## Configuration

At startup _CaptuRadio_ reads all configuration data from the configuration
file. It looks for it at

  * ./capturadiorc (in the current directory)
  * ~/.capturadio/capturadiorc
  * ~/.capturadiorc'
  * /etc/capturadiorc

If this file does not exist, then `~/.capturadio/capturadiorc` is created using defult values.

The stations is defined in the section `[stations]`. Every entry consists of a key-value-pair
defining the station identifier and the MP3 stream URL.

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
    logo_url = http://example.net/media/images/logo_256.png
    link_url = http://example.net/station1/

Every show can be defined in an configuration section.
You define the name of the show, it's duration and the station presenting this show. The station id
is used to find the correct stream url. If your provide a link_url for the show, the this is included
in the RSS feed to find further information on the web while listening to the show.

    [show1]
    title = The ultimate radio show
    duration = 1h55m
    station = station1
    link_url = http://example.net/shows/show1/

## Downloads

Git clone _CaptuRadio_ from GitHub at https://github.com/DirkR/capturadio

## License

The _CaptuRadio_ code is Freeware.

## Version History

### Version 0.9 -- 2014-03-XX

* The script 'create_podcast_feed.py' has been incorporated into the
  'recorder.py' script. Run 'recorder.py feed update' regulary.
* The command line interface has been changed completely.
  The former arguments do not work anymore. See `recorder.py help
  show capture` for details.
* The configuration file can be placed on different locations:

    * ./capturadiorc (in the current directory)
    * ~/.capturadio/capturadiorc
    * ~/.capturadiorc'
    * /etc/capturadiorc

If no configuration file can be found, then a new will be created at
`~/.capturadio/capturadiorc`.

#### Version 0.7 -- 2012-02-14

* Rewritten configuration management
* URLs of station logos (png or jpeg) and a default logo url can be defined in configuration file.
* These logos are embeded in the ID3 information (APIC tag) of the mp3 file
* The logo urls are integrated as `<itunes:image>` elements in the channel
  header and item description of rss channel files.

#### Version 0.6 -- 2012-01-25

* create_podcast_feed.py also uses the configuration file, there's a section `[feed]` provides
  information for the RSS file.
* MP3 files now contain the timestamp in their filename
* some small fixes

#### Version 0.5 -- 2012-01-24

Initial release.
