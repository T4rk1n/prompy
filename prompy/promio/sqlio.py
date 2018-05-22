import threading
import functools

from prompy.promise import Promise


class SqliteIO:
    def __init__(self, prom_type=Promise):
        self._lock = threading.Lock()

    def lock_wrap(self, func):
        @functools.wraps(func)
        def _wrap(*args, **kwargs):
            self._lock.acquire()
            ret = func(*args, **kwargs)
            self._lock.release()
            return ret
        return _wrap


