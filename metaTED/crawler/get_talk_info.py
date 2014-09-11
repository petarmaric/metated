# -*- coding: utf-8 -*-
import json
import logging
from lxml import html
from lxml.cssselect import CSSSelector
import re
import time


_HTML_ENTITY_RE = re.compile(r'&(#?[xX]?[0-9a-fA-F]+|\w{1,8});')
_INVALID_FILE_NAME_CHARS_RE = re.compile('[^\w\.\- ]+')

_VIDEO_PLAYER_DATA_SELECTOR = CSSSelector('div#talk + script')
_VIDEO_PLAYER_DATA_JSON_RE = re.compile('q\("talkPage.init",(.+)\)')
_VIDEO_PLAYER_DATA_TO_TALK_INFO = {
    'speaker': 'author',
    'event': 'event',
    'filmed': 'filming_year',
    'published': 'publishing_year',
    
    'name': 'file_base_name',
    
    'nativeDownloads': 'native_downloads',
    'subtitledDownloads': 'subtitled_downloads',
}
GROUP_DOWNLOADS_BY = ('author', 'event', 'filming_year', 'publishing_year')

AVAILABLE_VIDEO_QUALITIES = ('low', 'high')

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

def get_talk_info(talk_url):
    """
    Parses video player data to extract talk info. Sets 'Unknown' for unparsable
    data.
    """
    document = html.parse(talk_url)
    talk_info = dict.fromkeys(_VIDEO_PLAYER_DATA_TO_TALK_INFO.values(), 'Unknown')
    
    elements = _VIDEO_PLAYER_DATA_SELECTOR(document)
    if elements:
        match = _VIDEO_PLAYER_DATA_JSON_RE.match(elements[0].text)
        if match:
            video_player_data = json.loads(match.group(1))
            data = video_player_data['talks'][0]
            
            if data['external']: # Downloads not hosted by TED!
                raise ExternallyHostedDownloads(talk_url)
            
            for data_key, talk_info_key in _VIDEO_PLAYER_DATA_TO_TALK_INFO.items():
                if data_key in data:
                    x = data[data_key]
                    
                    if isinstance(x, (str, unicode)):
                        # Any string-like parsed data should be cleaned up, as
                        # it may later used for a piece of file name.
                        # Also, when extracting `file_base_name` replace the 1st
                        # colon with ' - ' to prettify the file name.
                        x = _clean_up_file_name(
                            x,
                            replace_first_colon_with_dash=(talk_info_key=='file_base_name')
                        )
                    elif data_key in ('filmed', 'published'):
                        # Extract year from Unix timestamp
                        x = time.gmtime(x).tm_year
                    
                    talk_info[talk_info_key] = x
    
    for k in _VIDEO_PLAYER_DATA_TO_TALK_INFO.values():
        if talk_info[k] == 'Unknown':
            logging.warning("Failed to guess the %s of '%s'", k, talk_url)
    
    if talk_info['native_downloads'] in (None, 'Unknown'):
        raise NoDownloadsFound(talk_url)
    
    if not talk_info['subtitled_downloads']:
        talk_info['subtitled_downloads'] = {} # JSON may return `None`, thus normalize it
        logging.warning("Failed to find any subtitles for '%s'", talk_url)
    
    return talk_info
