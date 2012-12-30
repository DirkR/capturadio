import PyRSS2Gen

class ItunesRSS(PyRSS2Gen.RSS2):
    """This class adds the "itunes" extension (<itunes:image>, etc.) to the rss feed."""

    rss_attrs = {
        "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        "version": "2.0",
    }

    def publish_extensions(self, handler):
        # implement this method to embed the <itunes:*> elements into the channel header.
        if self.image is not None and isinstance(self.image, PyRSS2Gen.Image) and self.image.url is not None:
            handler.startElement('itunes:image',  {'href': self.image.url})
            handler.endElement('itunes:image')


class ItunesRSSItem(PyRSS2Gen.RSSItem):
    """This class adds the "itunes" extension (<itunes:image>, etc.) to the rss feed item."""

    def publish_extensions(self, handler):
        # implement this method to embed the <itunes:*> elements into the channel header.
        if self.length is not None:
            PyRSS2Gen._opt_element(handler, "itunes:duration", self.length)
        if self.image is not None and isinstance(self.image, PyRSS2Gen.Image) and self.image.url is not None:
            handler.startElement('itunes:image',  {'href': self.image.url})
            handler.endElement('itunes:image')
