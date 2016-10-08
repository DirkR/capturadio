# -*- coding: utf-8 -*-
"""Collection of routines to generate files"""
import os
import time
import operator
import logging

import jinja2

from capturadio import version_string

def generate_feed(config, db, entity):
    """
    Write the list of files as RSS formatted file.

    The argument 'path' points to the folder, where the file will
    be written to. The name of the file is specified in
    config.feed['filename'] and defaults to 'rss.xml'.
    """
    this_dir = os.path.dirname(__file__)
    templates_dir = os.path.join(this_dir, 'templates')
    j2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        trim_blocks=True,
    )

    items = []
    for (key, value) in db.items():
        if entity.slug == "" or key.startswith(entity.slug):
            items.append(value)

    if len(items) == 0:
        # logging.warning('Skipped "{}" because of empty db'.format(entity.slug))
        return

    logging.debug("Generating feed for {}".format(entity.slug if entity.slug is not "" else '<root>'))
    items = sorted(items, key=operator.attrgetter('starttime'), reverse=True)
    contents = j2_env.get_template('feed.xml.jinja2').render(
        feed=entity,
        items=items,
        title=config.feed['title'],
        base_url=config.feed['base_url'],
        build_date=time.strftime('%c', time.localtime()),
        generator='CaptuRadio v{}'.format(version_string),
    )
    filename = os.path.join(entity.filename, 'rss.xml')
    with open(filename, "w") as rssfile:
        rssfile.write(contents)
