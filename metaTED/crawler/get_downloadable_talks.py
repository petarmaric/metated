import logging
from concurrent import futures
from multiprocessing import cpu_count
from metaTED.cache import cached_storage
from metaTED.crawler.get_talk_info import get_talk_info, ExternallyHostedDownloads, NoDownloadsFound
from metaTED.crawler.get_talks_urls import get_talks_urls


_PAGINATE_BY = 20


class NoDownloadableTalksFound(Exception):
    pass


def get_downloadable_talks(num_workers=None):
    talks_urls = get_talks_urls()
    
    talks_info = cached_storage.get('talks_infos', {})
    downloadable_talks = []
    new_talks_urls = []
    for talk_url in talks_urls:
        if talk_url in talks_info:
            downloadable_talks.append(talks_info[talk_url])
        else:
            new_talks_urls.append(talk_url)
    
    if not new_talks_urls:
        logging.info('No new talk urls found')
    else:
        num_new_talks = len(new_talks_urls)
        logging.info("Found %d new talk url(s)", num_new_talks)
        
        if num_workers is None:
            num_workers = 2*cpu_count() # Network IO is the bottleneck
        with futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_to_url = dict(
                (executor.submit(get_talk_info, talk_url), talk_url)
                for talk_url in new_talks_urls
            )
            
            for index, future in enumerate(futures.as_completed(future_to_url), start=1):
                if index % _PAGINATE_BY == 1:
                    logging.info(
                        "Getting download information on %d of %d talks...",
                        index,
                        num_new_talks
                    )
                
                talk_url = future_to_url[future]
                if future.exception() is not None:
                    e = future.exception()
                    if isinstance(e, ExternallyHostedDownloads):
                        logging.info(
                            "Downloads for '%s' are not hosted by TED, skipping",
                            talk_url
                        )
                    elif isinstance(e, NoDownloadsFound):
                        logging.error("No downloads for '%s', skipping", talk_url)
                    else:
                        logging.error("Skipping '%s', reason: %s", talk_url, e)
                else:
                    talk_info = future.result()
                    downloadable_talks.append(talk_info)
                    talks_info[talk_url] = talk_info
        
        cached_storage['talks_infos'] = talks_info
    
    if not downloadable_talks:
        raise NoDownloadableTalksFound('No downloadable talks found')
    
    logging.info(
        "Found %d downloadable talks in total",
        len(downloadable_talks)
    )
    return downloadable_talks
