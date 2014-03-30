"""Fixtures for capturadio tests"""

import pytest

@pytest.fixture
def test_folder(request, tmpdir):
  olddir = tmpdir.chdir()
  request.addfinalizer(olddir.chdir)
  tmpdir.join('capturadiorc').write('''
[settings]
destination = {0}/demodata
date_pattern = %d.%m.%Y
comment_pattern:  Show: %show
  Date: %date
  Website: %link_url
  Copyright: %year %station

[stations]
dlf = http://example.org/dlf
dkultur = http://example.org/dkultur
wdr2 = http://example.org/wdr2

[feed]
url = http://my.example.org
title = Internet Radio Recordings
about_url = http://my.example.org/about.html
description = Recordings
language = en
filename = rss.xml
default_logo_url = http://example.org/default.png
default_logo_copyright = A Creative Commons license

[dlf]
name = Deutschlandfunk
link_url = http://example.org/dlf
logo_url = http://example.org/dlf.png
date_pattern = %d.%m.%Y %H:%M

[nachtradio]
title = Nachtradio
duration = 3300
link_url = http://example.org/nachtradio
logo_url = http://example.org/nachtradio.png
station = dlf

[weather]
title = Weather forecast
duration = 300
logo_url = http://example.org/weather.png
station = dlf

[wdr2]
title = WDR 2
link_url = http://example.org/wdr2
logo_url = http://example.org/wdr2.png

[news]
title = Latest news
duration = 300
link_url = http://example.org/wdr2/news
logo_url = http://example.org/wdr2/news.png
station = wdr2
date_pattern = %Y-%m-%d
'''.format(str(tmpdir)))
  return tmpdir

@pytest.fixture
def config(request, test_folder):
  from capturadio import Configuration
  __config = Configuration(reset = True, folder=str(test_folder))
  return __config


