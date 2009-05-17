import os
import logging
from jinja2 import Environment, PackageLoader
from metaTED import __version__
from metaTED.cache import cached_storage
from metaTED.crawler.get_downloadable_talks import get_downloadable_talks
from metaTED.crawler.get_talk_info import AVAILABLE_VIDEO_QUALITIES

try:
    from email.utils import formatdate
except ImportError:
    from email.Utils import formatdate # Python 2.4 fallback


_METALINK_BASE_URL = "http://metated.petarmaric.com/metalinks/%s"


def _get_downloads(downloadable_talks, quality, group_by=None):
    downloads = []
    for talk_info in downloadable_talks:
        quality_info = talk_info['qualities'][quality]
        
        # Calculate full file path
        file_name = quality_info['file_name']
        if group_by:
            full_file_path = "%s/%s" % (talk_info[group_by], file_name)
        else:
            full_file_path = file_name
        
        downloads.append({
            'download_url': quality_info['download_url'],
            'full_file_path': full_file_path
        })
    return downloads


def _get_metalink_file_name(quality, group_by):
    group_part = group_by and "-grouped-by-%s" % group_by or ''
    return "TED-talks%s-in-%s-quality.metalink" % (group_part, quality)


def _get_metalink_description(quality, group_by):
    group_part = group_by and " grouped by %s" % group_by or ''
    return "Download TED talks%s encoded in %s quality" % (group_part, quality)


def _get_group_downloads_by(downloadable_talks):
    # Also generate metalinks with no grouped downloads
    groups = [None]
    # Extract talk_info metadata
    metadata = downloadable_talks[0].keys()
    # Guess possible groupings from talk_info metadata
    groups.extend(metadata)
    # Can't group by qualities metadata
    groups.remove('qualities')
    
    logging.debug("Downloads can be grouped by '%s'", groups)
    return groups


def generate_metalinks(output_dir=None):
    output_dir = os.path.abspath(output_dir or '')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Make sure downloadable_talks can be calculated
    downloadable_talks = get_downloadable_talks()
    
    # Prepare the template upfront, because it can be reused between metalinks
    env = Environment(loader=PackageLoader('metaTED'))
    template = env.get_template('template.metalink')

    # Use the same dates/times for all metalinks because they should, in my
    # opinion, point out when the metalinks were being generated and not when
    # they were physically written do disk
    refresh_date = formatdate()
    first_published_on = cached_storage.get('first_published_on')
    if first_published_on is None:
        cached_storage['first_published_on'] = first_published_on = refresh_date
    
    # Generate all metalink variants
    metalinks = []
    for group_by in _get_group_downloads_by(downloadable_talks):
        for quality in AVAILABLE_VIDEO_QUALITIES.keys():
            metalink_file_name = _get_metalink_file_name(quality, group_by)
            metalink_url = _METALINK_BASE_URL % metalink_file_name
            metalink_description = _get_metalink_description(quality, group_by)
            logging.debug("Generating '%s' metalink...", metalink_file_name)
            template.stream({
                'metalink_url': metalink_url,
                'metaTED_version': __version__,
                'first_published_on': first_published_on,
                'refresh_date': refresh_date,
                'description': metalink_description,
                'talks': _get_downloads(downloadable_talks, quality, group_by)
            }).dump(
                os.path.join(output_dir, metalink_file_name),
                encoding='utf-8'
            )
            metalinks.append({
                'download_url': metalink_url,
                'description': metalink_description
            })
            logging.info("Generated '%s' metalink", metalink_file_name)
    return {
        'metaTED_version': __version__,
        'first_published_on': first_published_on,
        'refresh_date': refresh_date,
        'num_downloadable_talks': len(downloadable_talks),
        'metalinks': metalinks
    }
