import datetime
import logging
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request

from mutagenx._id3frames import \
    TIT2, TDRC, TCON, TALB, TLEN, TPE1, TCOP, COMM, TCOM, APIC
from mutagenx.mp3 import MP3
from mutagenx.id3 import ID3, error

from capturadio.config import Configuration
from capturadio.entities import Episode


class Recorder(object):

    def capture(self, config, show):
        logging.debug('capture "{}"'.format(show))
        episode = Episode(config, show)
        try:
            self._write_stream_to_file(episode)
            self._add_metadata(episode)
            return episode
        except Exception as e:
            logging.error("Could not complete capturing, because an exception occured: {}".format(e))
            raise e

    def _write_stream_to_file(self, episode):
        not_ready = True
        logging.debug("write {} to {}".format(
            episode.stream_url, episode.filename
        ))
        try:
            dirname = os.path.dirname(episode.filename)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)

            with open(episode.filename, 'wb') as file:
                stream = urlopen(episode.stream_url)
                starttimestamp = time.mktime(episode.starttime)
                while not_ready:
                    try:
                        file.write(stream.read(10240))
                        if time.time() - starttimestamp > episode.duration:
                            not_ready = False
                    except KeyboardInterrupt:
                        logging.warning('Capturing interupted.')
                        not_ready = False

            episode.duration = time.time() - starttimestamp
            episode.duration_string = str(datetime.timedelta(seconds=episode.duration))
            episode.filesize = str(os.path.getsize(episode.filename))
            episode.mimetype = 'audio/mpeg'
            return episode

        except UnicodeDecodeError as e:
            logging.error("Invalid input: {} ({})".format(e.reason, e.object[e.start:e.end]))
            os.remove(episode.filename)
            raise e

        except HTTPError as e:
            logging.error("Could not open URL {} ({:d}): {}".format(episode.stream_url, e.code, e.msg))
            os.remove(episode.filename)
            raise e

        except IOError as e:
            logging.error("Could not write file {}: {}".format(episode.filename, e))
            os.remove(episode.filename)
            raise e

        except Exception as e:
            logging.error("Could not capture show, because an exception occured: {}".format(e))
            os.remove(episode.filename)
            raise e

    def _add_metadata(self, episode):
        if episode.filename is None:
            raise "filename is not set - you cannot add metadata to None"

        episode.description = 'Show: {show}<br>Date: {date}<br>Copyright: {year} <a href="{link_url}">{station}</a>'.format(
            show=episode.show.name,
            date=episode.pubdate,
            year=time.strftime('%Y', episode.starttime),
            station=episode.station.name,
            link_url=episode.link_url
        )

        config = Configuration()
        comment = config.comment_pattern % {
            'show': episode.show.name,
            'date': episode.pubdate,
            'year': time.strftime('%Y', episode.starttime),
            'station': episode.station.name,
            'link_url': episode.link_url
        }

        audiofile = MP3(episode.filename, ID3=ID3)
        # add ID3 tag if it doesn't exist
        try:
            audiofile.add_tags()
        except error:
            pass

        audiofile.tags.add(TIT2(encoding=2, text=[episode.name]))
        audiofile.tags.add(TDRC(encoding=2, text=[episode.pubdate]))
        audiofile.tags.add(TCON(encoding=2, text=['Podcast']))
        audiofile.tags.add(TALB(encoding=2, text=[episode.show.name]))
        audiofile.tags.add(TLEN(encoding=2, text=[episode.duration * 1000]))
        audiofile.tags.add(TPE1(encoding=2, text=[episode.station.name]))
        audiofile.tags.add(TCOP(encoding=2, text=[episode.station.name]))
        audiofile.tags.add(COMM(encoding=2, lang='eng', desc='desc', text=comment))
        audiofile.tags.add(TCOM(encoding=2, text=[episode.link_url]))
        self._add_logo(audiofile, episode.logo_url)
        audiofile.save()

    def _add_logo(self, audiofile, url):
        # APIC part taken from http://mamu.backmeister.name/praxis-tipps/pythonmutagen-audiodateien-mit-bildern-versehen/
        if url is not None:
            request = Request(url)
            request.get_method = lambda: 'HEAD'
            try:
                response = urlopen(request)
                logo_type = response.getheader('Content-Type')

                if logo_type in ['image/jpeg', 'image/png', 'image/gif']:
                    img = APIC(
                        encoding=3,  # 3 is for utf-8
                        mime=logo_type,
                        type=3,  # 3 is for the cover image
                        desc='Station logo',
                        data=urlopen(url).read()
                    )
                    audiofile.tags.add(img)
            except Exception as e:
                message = "Error during embedding logo %s - %s" % (url, e)
                logging.error(message)
