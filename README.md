# CaptuRadio

by Dirk Ruediger <<dirk@niebegeg.net>>

## Introduction

_CaptuRadio_ is a tool to record shows from internet radio stations
to your computer or server.  It is written in Python and primary
made to run on a server.
_CaptuRadio_ has only been tested on unix-like OSes, like MacOSX and Linux.


### Prerequisites

_CaptuRadio_ needs Python 3.x (tested using Python 3.4) and an unix-like operation system running on your machine.
The following python libraries need to be installed beside Python to run CapturRadio:

* mutagenx -- a Python module to handle audio metadata
  https://pypi.python.org/pypi/mutagenx, tested with version 1.24
* docopt -- a Python module to handle arguments parsing of cli
  applications, version 0.6 and above
* Jinja2 -- a template engine written in pure python
  https://pypi.python.org/pypi/Jinja2, version 2.6 and above
* xdg -- Support for the XDG Base Directory Specification
  https://pypi.python.org/pypi/xdg, tested with version 1.0

### Installation

Install the application by running the setup script:

    pip3 install -r requirements.txt
    python3 setup.py install

The app needs a configuration file. Simply run

    recorder config setup

and it will create a configuration at `~/.config/capturadio`.
You should edit the file and customize it. Especially the destination folder
and the base_url should be adopted.

If you updated the codebase, then runn the following command to update the
configuration:

    recorder config update

Run the command

    recorder config list

to see the current configuration.

## Usage

_CaptuRadio_ needs some information on the commandline to operate correctly.

    recorder show capture <show>

records a pre-defined radio show.
The option `show` tells _CaptuRadio_ which station should be recorded. The show name has
to be defined in `~/.local/capturadio` (see section `Configuration` below).

    recorder config list

This command lists all defined confuration values.

    recorder feed update

By running this command the files providing the RSS feeds are
regenerated.

See `recorder help <command>` for more information on a specific command.

## Configuration

At startup _CaptuRadio_ reads all configuration data from the configuration
file. It looks for it at `~/.local/capturadio`. If this file does not exist,
then it is created using defult values.

The stations are defined in the section `[stations]`. Every entry consists of a key-value-pair
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

### Version 0.11 -- 2017-01-29

CaptuRadio had it's 5th birthday last week - time for a new release.

 * Rendering a HTML version of the feeds
 * Updated RSS feed file structure
 * Command 'feed list' lists all episodes from episodes_db
 * Command 'config update' migrates mp3 files in podcasts folder into entries in
   episodes database.
 * Project structure re-organized.

Warning: Due to the Upgrade to Python3 it is no longer possible to capture
Icecast streams. The urllib library is more strict when parsing the HTTP
responses.

### Version 0.10 -- 2016-10-06

* Ported to Python3, it will no longer run on Python 2.x
* PyRSSGen is replaced by Jinja2 to generate output files
* Episodes are stored in a database, so the episode metadata
  don't have to be retrieved from ID3 tags
* Support for the XDG Base Directory Specification, using
  XDG_CONFIG_HOME and XDG_APP_HOME for configuration and databases
* Configuration file is located at `~/.local/capturadio` and
  will bemoved there, if one is found at legacy locations.
* Major code cleanup

### Version 0.9 -- 2014-03-27

* The script 'create_podcast_feed.py' has been incorporated into the
  'recorder' script. Run 'recorder feed update' regulary.
* The command line interface has been changed completely.
  The former arguments do not work anymore. See `recorder help
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
