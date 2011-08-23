import logging
import re
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup
from metaTED import SITE_URL
from metaTED.crawler import urlread


TALKS_LIST_URL = "http://www.ted.com/talks/quick-list"
TOTAL_TALKS_RE = re.compile("Showing \d+ - \d+ of\s+(\d+)")


TALKS_URLS_BLACKLIST = [
    # No downloads
    'http://www.ted.com/talks/rokia_traore_sings_m_bifo.html',
    'http://www.ted.com/talks/rokia_traore_sings_kounandi.html',
]


def get_talks_urls():
    logging.debug('Looking for talk urls...')
    soup = BeautifulSoup(urlread(TALKS_LIST_URL))
    talks_table = soup.find('table', 'downloads')
    talks_urls = [
        urljoin(SITE_URL, tr.findAll('td')[2].a['href'])
        for tr in talks_table.findAll('tr')[1:] # Skip 1st 'tr', used as header
    ]
    
    # Remove the well-known problematic talk URLs (i.e. no downloads available)
    talks_urls = [url for url in talks_urls if url not in TALKS_URLS_BLACKLIST]
    
    logging.info("Found %d talk url(s) in total", len(talks_urls))
    return talks_urls
