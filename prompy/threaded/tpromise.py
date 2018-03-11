import os

from prompy.promise import Promise
from prompy.promutils import promise_wrap
from prompy.threaded.promise_queue import PromiseQueuePool

# GLOBAL THREAD POOL

_prom_pool_size = os.getenv('PROMPY_THREAD_POOL_SIZE', 2)
_prom_thread_idle_time = os.getenv('PROMPY_THREAD_IDLE_TIME', 2)

_prom_pool = PromiseQueuePool(start=True, pool_size=_prom_pool_size, max_idle=_prom_thread_idle_time)


class TPromise(Promise):
    """A promise with auto insert in a threaded promise queue."""
    __promise_pool = _prom_pool

    def __init__(self, starter, *args, **kwargs):
        super().__init__(starter, *args, **kwargs)
        self.__promise_pool.add_promise(self)

    @classmethod
    def stop_queue(cls):
        cls.__promise_pool.stop()

    @staticmethod
    def wrap(func):
        return promise_wrap(func, prom_type=TPromise)
