import logging
from email.utils import formatdate
from jinja2 import Environment, PackageLoader
from metaTED import __version__
from metaTED.cache import cached_storage
from metaTED.crawler.get_talk_info import AVAILABLE_VIDEO_QUALITIES


def _get_downloads(talk_infos, quality, group_by=None):
    downloads = []
    for talk_info in talk_infos:
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


def _get_group_downloads_by(talk_infos):
    # Also generate metalinks with no grouped downloads
    groups = [None]
    
    # Guess possible groupings from talk_info metadata
    groups.extend(talk_infos[0].keys())
    groups.remove('qualities')
    
    logging.debug("Downloads can be grouped by '%s'", groups)
    return groups


def generate_metalinks(talk_infos):
    refresh_date = formatdate()
    first_published_on = cached_storage.get('first_published_on')
    if first_published_on is None:
        cached_storage['first_published_on'] = first_published_on = refresh_date
    
    env = Environment(loader=PackageLoader('metaTED'))
    template = env.get_template('template.metalink')

    for group_by in _get_group_downloads_by(talk_infos):
        for quality in AVAILABLE_VIDEO_QUALITIES.keys():
            metalink_file_name = _get_metalink_file_name(quality, group_by)
            logging.debug("Generating '%s' metalink...", metalink_file_name)
            template.stream({
                'metalink_file_name': metalink_file_name,
                'metaTED_version': __version__,
                'first_published_on': first_published_on,
                'refresh_date': refresh_date,
                'quality': quality,
                'group_by': group_by,
                'talks': _get_downloads(talk_infos, quality, group_by)
            }).dump(metalink_file_name, encoding='utf-8')
            logging.info("Generated '%s' metalink", metalink_file_name)