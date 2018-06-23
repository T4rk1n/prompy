"""
Threaded Promise

Auto insert in a global thread pool.

Use the following environ vars:

* PROMPY_THREAD_POOL_SIZE=2
* PROMPY_THREAD_IDLE_TIME=0.5
* PROMPY_THREAD_DAEMON=false
"""
import os

from prompy.promise import Promise
from prompy.promtools import promise_wrap
from prompy.threadio.promise_queue import PromiseQueuePool

# GLOBAL THREAD POOL

_prom_pool_size = os.getenv('PROMPY_THREAD_POOL_SIZE', 2)
_prom_thread_idle_time = os.getenv('PROMPY_THREAD_IDLE_TIME', 0.5)

_prom_pool = PromiseQueuePool(pool_size=_pool_size, max_idle=_idle_time, daemon=_daemon)


class TPromise(Promise):
    """A promise with auto insert in a threadio.PromiseQueue."""
    __promise_pool = _prom_pool

    def __init__(self, starter, *args, **kwargs):
        super().__init__(starter, *args, **kwargs)
        self.__promise_pool.add_promise(self)

    @classmethod
    def stop_queue(cls):
        cls.__promise_pool.stop()

    @classmethod
    def wrap(cls, func):
        return promise_wrap(func, prom_type=cls)
