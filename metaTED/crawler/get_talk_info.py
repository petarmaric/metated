# -*- coding: utf-8 -*-
import logging
from lxml import html
from lxml.cssselect import CSSSelector
from lxml.etree import XPath
from os.path import splitext
import re
from urlparse import urljoin, urlsplit
from .get_talks_urls import TALKS_LIST_URL
from .. import SITE_URL


_HTML_ENTITY_RE = re.compile(r'&(#?[xX]?[0-9a-fA-F]+|\w{1,8});')
_INVALID_FILE_NAME_CHARS_RE = re.compile('[^\w\.\- ]+')

_EXTERNALLY_HOSTED_DOWNLOADS_SELECTOR = CSSSelector('div#external_player')

_AUTHOR_BIO_XPATH = XPath(u'//a[text()="Full bio »"]')

_EVENT_SELECTOR = CSSSelector('div.talk-meta span.event-name')

_THEME_SELECTOR = CSSSelector('ul.relatedThemes li a')

_TRANSCRIPT_LANGUAGES_SELECTOR = CSSSelector('select#languageCode option')

AVAILABLE_VIDEO_QUALITIES = {
    'low': 'Low',
    'standard': 'Regular',
    'high': 'High',
}
_VIDEO_QUALITIES_XPATH = XPath(
    '//a[@href=$relative_talk_url]/ancestor::node()[name()="tr"]/td[5]/a'
)

_YEARS_SELECTOR = CSSSelector('div.talk-meta')
_YEARS_RE_DICT = {
    'filming-year': re.compile('Filmed \w+ (\d+)'),
    'publishing-year': re.compile('Posted \w+ (\d+)'),
}


class NoDownloadsFound(Exception):
    pass


class ExternallyHostedDownloads(Exception):
    pass


def _clean_up_file_name(file_name, replace_first_colon_with_dash=False):
    if replace_first_colon_with_dash:
        # Turns 'Barry Schuler: Genomics' into 'Barry Schuler - Genomics'
        file_name = file_name.replace(': ', ' - ', 1)
    # Remove html entities
    file_name = _HTML_ENTITY_RE.sub('', file_name)
    # Remove invalid file name characters
    file_name = _INVALID_FILE_NAME_CHARS_RE.sub('', file_name)
    # Should be clean now
    return file_name

_talk_list_document_cache = None
def _get_talk_list_document():
    global _talk_list_document_cache
    
    if _talk_list_document_cache is None:
        _talk_list_document_cache = html.parse(TALKS_LIST_URL)
    
    return _talk_list_document_cache

def _guess_author(talk_url, document):
    """
    Tries to guess the author, or returns 'Unknown' if no author was found.
    """
    elements = _AUTHOR_BIO_XPATH(document)
    if elements:
        author_bio_url = urljoin(SITE_URL, elements[0].get('href'))
        author_bio_document = html.parse(author_bio_url)
        return _clean_up_file_name(
            author_bio_document.find('/head/title').text.split('|')[0].strip()
        )
    
    logging.warning("Failed to guess the author of '%s'", talk_url)
    return 'Unknown'

def _guess_event(talk_url, document):
    """
    Tries to guess the talks event, or returns 'Unknown' if no event was found.
    """
    elements = _EVENT_SELECTOR(document)
    if elements:
        return _clean_up_file_name(elements[0].text)
    
    logging.warning("Failed to guess the event of '%s'", talk_url)
    return 'Unknown'

def _guess_theme(talk_url, document):
    """
    Tries to guess the talks theme, or returns 'Unknown' if no theme was found.
    """
    elements = _THEME_SELECTOR(document)
    if elements:
        return _clean_up_file_name(elements[0].text)
    
    logging.warning("Failed to guess the theme of '%s'", talk_url)
    return 'Unknown'

def _get_subtitle_languages_codes(talk_url, document):
    """
    Returns a list of all subtitle language codes for a given talk URL. 
    """
    language_codes = [
        opt.get('value')
        for opt in _TRANSCRIPT_LANGUAGES_SELECTOR(document)
        if opt.get('value') != ''
    ]
    
    if not language_codes:
        logging.warning("Failed to find any subtitles for '%s'", talk_url)
    
    return language_codes

def _get_download_urls_dict(talk_url):
    """
    Returns a dictionary of all download URLs for a given talk URL, mapping 
    quality marker to the download URL.
    """
    return dict(
        (a.text.strip(), urljoin(SITE_URL, a.get('href')))
        for a in _VIDEO_QUALITIES_XPATH(
            _get_talk_list_document(),
            relative_talk_url=urlsplit(talk_url).path
        )
    )

def _guess_year(name, regexp, talk_url, document):
    elements = _YEARS_SELECTOR(document)
    if elements:
        match = regexp.search(elements[0].text_content())
        if match:
            return _clean_up_file_name(match.group(1))
    
    logging.warning("Failed to guess the %s of '%s'", name, talk_url)
    return 'Unknown'

def get_talk_info(talk_url):
    document = html.parse(talk_url)
    file_base_name = _clean_up_file_name(
        document.find('/head/title').text.split('|')[0].strip(),
        replace_first_colon_with_dash=True
    )
    
    # Downloads not hosted by TED!
    if _EXTERNALLY_HOSTED_DOWNLOADS_SELECTOR(document):
        raise ExternallyHostedDownloads(talk_url)
    
    # Try to find download URLs for all qualities
    qualities_found = []
    qualities_missing = []
    qualities = {}
    quality_marker_to_download_url = _get_download_urls_dict(talk_url)
    for name, marker in AVAILABLE_VIDEO_QUALITIES.items():
        download_url = quality_marker_to_download_url.get(marker)
        if download_url:
            qualities_found.append(name)
            qualities[name] = {
                'download_url': download_url,
                'file_name': "%s%s" % (
                    file_base_name,
                    splitext(urlsplit(download_url).path)[1]
                )
            }
        else:
            logging.error(
                "Failed to find the %s quality download URL for '%s'",
                name,
                talk_url
            )
            qualities_missing.append(name)
    
    if not qualities_found: # No downloads found!
        raise NoDownloadsFound(talk_url)
    
    if qualities_missing: # Some found, but not all
        # Use what you got, emulate the rest with the first discovered quality
        emulator_name = qualities_found[0]
        emulator = qualities[emulator_name]
        for name in qualities_missing:
            qualities[name] = emulator
            logging.warn(
                "Emulating %s quality with %s quality for '%s'",
                name,
                emulator_name,
                talk_url
            )
    
    talk_info = {
        'author': _guess_author(talk_url, document),
        'theme': _guess_theme(talk_url, document),
        'language-codes': _get_subtitle_languages_codes(talk_url, document),
        'qualities': qualities,
    }
    talk_info.update(
        (name, _guess_year(name, regexp, talk_url, document))
        for name, regexp in _YEARS_RE_DICT.items()
    )
    return talk_info
