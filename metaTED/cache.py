import os
from shove import Shove
from shove.store.file import FileStore


cached_storage = Shove(
    store=FileStore(os.path.expanduser('~/.metaTED/cache')),
    cache='simplelru://'
)

cache = cached_storage._cache