from concurrent import futures
import logging
from multiprocessing import cpu_count
from lxml import html
from lxml.cssselect import CSSSelector
from urlparse import urljoin
from .. import SITE_URL
from ..cache import cached_storage


TALKS_LIST_URL_FMT = "http://www.ted.com/talks/quick-list?page=%d"

_PAGINATION_INFO_SELECTOR = CSSSelector('div.pagination a:nth-last-of-type(1)')

_TALKS_URLS_SELECTOR = CSSSelector('div.quick-list__row div.title span a')


TALKS_URLS_BLACKLIST = [
    # No downloads
    'http://www.ted.com/talks/rokia_traore_sings_m_bifo.html',
    'http://www.ted.com/talks/rokia_traore_sings_kounandi.html',
    'http://www.ted.com/talks/andrew_stanton_the_clues_to_a_great_story.html',
]


def _parse_page(page_num):
    return html.parse(TALKS_LIST_URL_FMT % page_num)

def _get_num_pages():
    logging.debug('Trying to find out the number of talk list pages...')
    elements = _PAGINATION_INFO_SELECTOR(_parse_page(1))
    num_pages = int(elements[0].text_content())
    logging.info("Found %d talk list page(s)", num_pages)
    return num_pages

def _get_talks_urls_from_page(page_num):
    logging.debug("Looking for talk urls on page #%d", page_num)
    talks_urls = [
        urljoin(SITE_URL, a.get('href'))
        for a in _TALKS_URLS_SELECTOR(_parse_page(page_num))
    ]
    logging.info("Found %d talk url(s) on page #%d", len(talks_urls), page_num)
    return talks_urls
 
def _get_talks_urls():
    logging.debug('Looking for talk urls...')
    
    num_workers = 2*cpu_count() # Network IO is the bottleneck
    with futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        talks_urls = sum(executor.map(
            _get_talks_urls_from_page,
            xrange(1, _get_num_pages()+1) # Talk list pages are 1-indexed
        ), [])
    
    # Remove the well-known problematic talk URLs (i.e. no downloads available)
    talks_urls = [url for url in talks_urls if url not in TALKS_URLS_BLACKLIST]
    
    logging.info("Found %d talk url(s) in total", len(talks_urls))
    return talks_urls

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
            if num_talks and num_talks == len(_get_talks_urls_from_page(num_pages)):
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
