import logging
from metaTED.crawler.get_talk_info import get_talk_info, NoDownloadsFound
from metaTED.crawler.get_talks_urls import get_talks_urls


_PAGINATE_BY = 20


def get_downloadable_talks():
    talks_urls = get_talks_urls()
    num_urls = len(talks_urls)
    downloadable_talks = []
    for index, talk_url in enumerate(talks_urls):
        try:
            if index % _PAGINATE_BY == 0:
                logging.info(
                    "Getting download information on %d of %d talks...",
                    index+1,
                    num_urls
                )
            downloadable_talks.append(get_talk_info(talk_url))
        except NoDownloadsFound, e:
            logging.error("No downloads for '%s', skipping", talk_url)
        except Exception, e:
            logging.error("Skipping '%s', reason: %s", talk_url, e)
    logging.info(
        "Found %d downloadable talks in total",
        len(downloadable_talks)
    )
    return downloadable_talks
