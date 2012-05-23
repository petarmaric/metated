import logging
from lxml import html
from lxml.cssselect import CSSSelector
from urlparse import urljoin
from .. import SITE_URL


TALKS_LIST_URL = "http://www.ted.com/talks/quick-list"
_TALKS_URLS_SELECTOR = CSSSelector('table.downloads tr td:nth-child(3) a')


TALKS_URLS_BLACKLIST = [
    # No downloads
    'http://www.ted.com/talks/rokia_traore_sings_m_bifo.html',
    'http://www.ted.com/talks/rokia_traore_sings_kounandi.html',
    'http://www.ted.com/talks/andrew_stanton_the_clues_to_a_great_story.html',
]


def get_talks_urls():
    logging.debug('Looking for talk urls...')
    document = html.parse(TALKS_LIST_URL)
    talks_urls = [
        urljoin(SITE_URL, a.get('href'))
        for a in _TALKS_URLS_SELECTOR(document)
    ]
    
    # Remove the well-known problematic talk URLs (i.e. no downloads available)
    talks_urls = [url for url in talks_urls if url not in TALKS_URLS_BLACKLIST]
    
    logging.info("Found %d talk url(s) in total", len(talks_urls))
    return talks_urls
