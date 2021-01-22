# -*- coding: utf-8 -*-
"""Collection of routines to generate files"""
import os
import time
import operator
import logging

import jinja2

from capturadio import version_string


def generate_page(config, db, entity):
    """
    Write the list of files and folders (show, station) as HTML file.
    """
    this_dir = os.path.dirname(__file__)
    templates_dir = os.path.join(this_dir, 'templates')
    j2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        trim_blocks=True,
    )

    shows = []
    if 'shows' in entity.__dict__:
        for show in entity.shows:
            if not os.path.exists(show.filename):
                logging.debug("Skipping non-existant file {}".format(show.filename))
                continue

            _convert_logo_to_dataurl(config.icons_db, show)
            shows.append(_escape_string_attributes(show))

    items = []
    if len(shows) == 0:
        for (slug, episode) in db.items():
            if entity.slug == "" or slug.startswith(entity.slug):
                if not os.path.exists(episode.filename):
                    logging.debug("Skipping non-existant file {}".format(episode.filename))
                    continue

                _convert_logo_to_dataurl(config.icons_db, episode)
                items.append(_escape_string_attributes(episode))

    if len(items) == 0 and len(shows) == 0:
        # logging.warning('Skipped "{}" because of empty db'.format(entity.slug))
        return

    logging.debug("Generating feed for {}".format(entity.slug if entity.slug != "" else '<root>'))
    items = sorted(items, key=operator.attrgetter('starttime'), reverse=True)
    contents = j2_env.get_template('page.html.jinja2').render(
        feed=_escape_string_attributes(entity),
        shows=shows,
        items=items,
        title=config.feed['title'],
        base_url=config.feed['base_url'],
        build_date=time.strftime('%c', time.localtime()),
        generator='CaptuRadio v{}'.format(version_string),
    )
    filename = os.path.join(entity.filename, 'index.html')
    with open(filename, "w") as rssfile:
        rssfile.write(contents)


def _convert_logo_to_dataurl(icons_db, entity):
    logo_url = str.lower(entity.logo_url)
    if logo_url in icons_db.keys():
        item = icons_db[logo_url]
        entity.logo_url = "data:{};base64,{}".format(item['mimetype'], item['data'])
    else:
        mimetype, data = _get_imgurl_as_base64(entity.logo_url)
        icons_db[logo_url] = {
            'mimetype': mimetype,
            'data': data
        }
        entity.logo_url = "data:{};base64,{}".format(mimetype, data)


def _get_imgurl_as_base64(url):
    import urllib.request
    import base64

    local_filename, headers = urllib.request.urlretrieve(url)
    data = base64.b64encode(open(local_filename, "rb").read())
    mimetype = headers.get_content_type()
    return mimetype, data.decode('utf-8')

def generate_feed(config, db, entity):
    """
    Write the list of files as RSS formatted file.
    """
    this_dir = os.path.dirname(__file__)
    templates_dir = os.path.join(this_dir, 'templates')
    j2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        trim_blocks=True,
    )

    items = []
    for (slug, episode) in db.items():
        if entity.slug == "" or slug.startswith(entity.slug):
            if not os.path.exists(episode.filename):
                logging.warning("Skipping non-existant file {}".format(episode.filename))
                continue
            items.append(_escape_string_attributes(episode))

    if len(items) == 0:
        # logging.warning('Skipped "{}" because of empty db'.format(entity.slug))
        return

    logging.debug("Generating feed for {}".format(entity.slug if entity.slug != "" else '<root>'))
    items = sorted(items, key=operator.attrgetter('starttime'), reverse=True)
    slug = entity.slug + ("/" if entity.slug != '' else '') + 'rss.xml'
    contents = j2_env.get_template('feed.xml.jinja2').render(
        feed=_escape_string_attributes(entity),
        items=items,
        title=config.feed['title'],
        base_url=config.feed['base_url'],
        slug=slug,
        build_date=time.strftime('%a, %d %b %Y %X %z', time.localtime()),
        generator='CaptuRadio v{}'.format(version_string),
    )
    filename = os.path.join(entity.filename, 'rss.xml')
    with open(filename, "w") as rssfile:
        rssfile.write(contents)


def _escape_string_attributes(entity):
    for attr in ('name', 'author'):
        if attr in entity.__dict__:
            entity.__dict__[attr + '_escaped'] = \
                entity.__dict__[attr].encode('ascii', 'xmlcharrefreplace').decode("utf-8")
    return entity
