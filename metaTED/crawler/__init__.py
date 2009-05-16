import logging
import urllib2
import metaTED
from metaTED.cache import cache


_DEFAULT_RETRY_TIMES = 5


_opener = urllib2.build_opener()
_opener.addheaders = [('User-agent', 'metaTED/%s' % metaTED.__version__)]


def urlread(fullurl, max_retries=_DEFAULT_RETRY_TIMES):
    # Check in-memory cache before requesting url
    logging.debug("Searching cache for '%s' contents...", fullurl)
    if fullurl in cache:
        logging.debug("Found the cached version of '%s' contents", fullurl)
        return cache[fullurl]
    logging.debug("Failed to find the cached version of '%s' contents", fullurl)

    saved_exception = None
    for try_num in xrange(1, max_retries+1):
        try:
            logging.debug(
                "Requesting '%s' (try %d of %d)...",
                fullurl,
                try_num,
                max_retries
            )
            data = _opener.open(fullurl).read()
            logging.debug("Successfully read data from '%s'", fullurl)
            cache[fullurl] = data
            return data
        except urllib2.URLError, e:
            if try_num == max_retries:
                log_func = logging.fatal
                message = "Giving up! Could not read data from '%s': %s"
                saved_exception = e
            else:
                log_func = logging.warning
                message = "Problem while trying to read data from '%s': %s"
            log_func(message, fullurl, e)
    
    # Re-raise the last exception because crawler used up all retries
    raise saved_exception