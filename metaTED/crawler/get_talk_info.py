import re
import logging
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup
from metaTED import SITE_URL
from metaTED.cache import cached_storage
from metaTED.crawler import urlread


AVAILABLE_VIDEO_QUALITIES = {
    'low': {
        'marker': 'Download video to desktop (MP4)',
        'file_extension': 'mp4',
    },
    'high': {
        'marker': 'Watch high-res video (MP4)',
        'file_extension': 'mp4',
    },
}


_HTML_ENTITY_RE = re.compile(r'&(#?[xX]?[0-9a-fA-F]+|\w{1,8});')
_INVALID_FILE_NAME_CHARS_RE = re.compile('[^\w\.\- ]+')
_FILMING_YEAR_RE = re.compile('fd:\"\w+ (\d+)\",')
_PUBLISHING_YEAR_RE = re.compile('pd:\"\w+ (\d+)\",')
_THEME_RE = re.compile('Other talks from &quot;(.+)&quot;')


class NoDownloadsFound(Exception):
    pass


def _clean_up_file_name(file_name, replace_first_colon_with_dash=False):
    if replace_first_colon_with_dash:
        # Turns 'Barry Schuler: Genomics' into 'Barry Schuler - Genomics'
        file_name = file_name.replace(': ', ' - ', 1)
    # Remove html enitites
    file_name = _HTML_ENTITY_RE.sub('', file_name)
    # Remove invalid file name characters
    file_name = _INVALID_FILE_NAME_CHARS_RE.sub('', file_name)
    # Should be clean now
    return file_name


def _guess_year(talk_url, soup):
    """
    Tries to guess the filming year, or if it's not available - the publishing
    year.
    
    Returns year as string, or 'Unknown' if no date was found.
    """
    year_txt = soup.find(id='videoPlayerSWF').findNextSibling('script').string
    match = _FILMING_YEAR_RE.search(year_txt)
    if match is None:
        logging.debug("Failed to guess the filming year of '%s'", talk_url)
        match = _PUBLISHING_YEAR_RE.search(year_txt)
    if match:
        return match.group(1)
    else:
        logging.warning(
            "Failed to guess both the publishing and filming year of '%s'",
            talk_url
        )
        return 'Unknown'


def _guess_author(talk_url, soup):
    """
    Tries to guess the author, or returns 'Unknown' if no author was found.
    """
    element = soup.find(id='tagline').findNextSibling('h3')
    if element:
        return _clean_up_file_name(element.string.split('About ', 1)[1])
    else:
        logging.warning(
            "Failed to guess the author of '%s'",
            talk_url
        )
        return 'Unknown'


def _guess_theme(talk_url, soup):
    """
    Tries to guess the talks theme, or returns 'Unknown' if no theme was found.
    """
    element = soup.find('div', 'related').h3
    if element:
        match = _THEME_RE.search(element.string)
        if match:
            return _clean_up_file_name(match.group(1), True)
    
    logging.warning(
        "Failed to guess the theme of '%s'",
        talk_url
    )
    return 'Unknown'


def _find_download_url(soup, quality_marker):
    """
    Returns download URL of a talk in requested video quality, or None if the
    talk can't be downloaded in that quality.
    """
    element = soup.find(text=quality_marker)
    return element and urljoin(SITE_URL, element.parent['href'])


def _get_talk_info(talk_url):
    soup = BeautifulSoup(urlread(talk_url))
    file_base_name = _clean_up_file_name(
        soup.html.head.title.string.split('|')[0].strip(),
        True
    )
    
    # Try to find download URLs for all qualities
    qualities_found = []
    qualities_missing = []
    qualities = {}
    for name, info in AVAILABLE_VIDEO_QUALITIES.items():
        download_url = _find_download_url(soup, info['marker'])
        if download_url:
            qualities_found.append(name)
            qualities[name] = {
                'download_url': download_url,
                'file_name': "%s.%s" % (file_base_name, info['file_extension'])
            }
        else:
            logging.error(
                "Failed to find the %s quality download URL for '%s'",
                name,
                talk_url
            )
            qualities_missing.append(name)

    if len(qualities_found) == 0: # No downloads found!
        raise NoDownloadsFound(talk_url)

    if len(qualities_missing) > 0: # Some found, but not all
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
    
    return {
        'year': _guess_year(talk_url, soup),
        'author': _guess_author(talk_url, soup),
        'theme': _guess_theme(talk_url, soup),
        'qualities': qualities,
    }


def get_talk_info(talk_url):
    talks_info = cached_storage.get('talks_infos', {})
    logging.debug("Searching cache for talk info on '%s'...", talk_url)
    if talk_url in talks_info:
        logging.debug("Found the cached version of '%s' talk info", talk_url)
        return talks_info[talk_url]
    
    # Cache miss
    logging.debug(
        "Failed to find the cached version of '%s' talk info, calculating.",
        talk_url
    )
    info = _get_talk_info(talk_url)
    talks_info[talk_url] = info
    cached_storage['talks_infos'] = talks_info
    return info
