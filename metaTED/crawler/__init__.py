import logging
import metaTED
import requests


_DEFAULT_RETRY_TIMES = 5


def urlread(fullurl, max_retries=_DEFAULT_RETRY_TIMES):
    saved_exception = None
    for try_num in xrange(1, max_retries+1):
        try:
            logging.debug(
                "Requesting '%s' (try %d of %d)...",
                fullurl,
                try_num,
                max_retries
            )
            r = requests.get(
                url=fullurl,
                headers={
                    'User-Agent': "metaTED/%s" % metaTED.__version__,
            })
            
            # Check if we made a bad request
            r.raise_for_status()
            
            logging.debug("Successfully read data from '%s'", fullurl)
            return r.content
        except requests.RequestException, e:
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
