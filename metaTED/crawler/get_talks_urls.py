import logging
import re
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup
from metaTED import SITE_URL
from metaTED.cache import cached_storage
from metaTED.crawler import urlread


TALKS_LIST_URLS = "http://www.ted.com/index.php/talks/list/page/%d"
TOTAL_PAGES_RE = re.compile("Showing page \d+ of (\d+)")


TALKS_URLS_BLACKLIST = [
    'http://www.ted.com/talks/rokia_traore_sings_m_bifo.html', # No downloads
    'http://www.ted.com/talks/rokia_traore_sings_kounandi.html', # No downloads
]


def _read_page(page_num):
    return urlread(TALKS_LIST_URLS % page_num)


def _get_num_pages():
    logging.debug('Trying to find out the number of talk list pages...')
    soup = BeautifulSoup(_read_page(1))
    num_pages = int(
        TOTAL_PAGES_RE.match(
            soup.find('p', text=TOTAL_PAGES_RE)
        ).group(1)
    )
    logging.info("Found %d talk list page(s)", num_pages)
    return num_pages


def _get_talks_urls_from_page(page_num):
    logging.debug("Looking for talk urls on page #%d", page_num)
    soup = BeautifulSoup(_read_page(page_num))
    urls = [urljoin(SITE_URL, h.a['href']) for h in soup.findAll('h4')]
    logging.info("Found %d talk url(s) on page #%d", len(urls), page_num)
    return urls


def _get_talks_urls():
    urls = []
    for page in xrange(1, _get_num_pages()+1): # Talk list pages are 1-indexed
        urls.extend(_get_talks_urls_from_page(page))
    
    # Remove the well-known problematic talk URLs (i.e. no downloads available)
    urls = filter(lambda x: x not in TALKS_URLS_BLACKLIST, urls)
    
    logging.info("Found %d talk url(s) in total", len(urls))
    return urls


def _check_talks_urls_cache():
    logging.info('Looking for a cached version of talk urls...')
    if 'talks_urls' in cached_storage:
        # Cached version of talk urls is considered valid if:
        # 1. Real number of talk list pages is equal to the cached number
        # 2. Real number of talk urls on the last list page is equal to the
        #    cached number
        logging.info('Found a cached version of talk urls. Validating...')
        num_pages = cached_storage.get('num_of_talk_list_pages')
        if num_pages and num_pages == _get_num_pages():
            num_talks = cached_storage.get('num_of_talks_urls_on_last_page')
            if num_talks and \
            num_talks == len(_get_talks_urls_from_page(num_pages)):
                logging.info('Found a valid cached version of talk urls')
                return True
        logging.warning('Cached version of talk urls is invalid')
        return False
    logging.info('Failed to find the cached version of talk url(s)')
    return False


def get_talks_urls():
    if not _check_talks_urls_cache():
        cached_storage['num_of_talk_list_pages'] = _get_num_pages()
        cached_storage['num_of_talks_urls_on_last_page'] = len(
            _get_talks_urls_from_page(cached_storage['num_of_talk_list_pages'])
        )
        cached_storage['talks_urls'] = _get_talks_urls()
    return cached_storage['talks_urls']
