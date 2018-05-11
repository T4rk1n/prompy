from prompy.promise import Promise
from prompy.networkio import urlcall
from prompy.threadio.promise_queue import PromiseQueuePool
from prompy.container import container_wrap


class PooledCaller:
    """
    Class wrapper for urlcall.
    Auto-add calls to a PromiseQueuePool to be resolved.
    """

    def __init__(self, **pool_kwargs):
        self._pool = PromiseQueuePool(**pool_kwargs)

    def call(self, url, **kwargs) -> Promise[urlcall.UrlCallResponse]:
        prom = urlcall.url_call(url, **kwargs)
        self._pool.add_promise(prom)
        return prom

    def json_call(self, url, **kwargs):
        prom = urlcall.json_call(url, **kwargs)
        self._pool.add_promise(prom)
        return prom

    def get(self, url, **kwargs):
        prom = urlcall.get(url, **kwargs)
        self._pool.add_promise(prom)
        return prom

    def post(self, url, **kwargs):
        prom = urlcall.post(url, **kwargs)
        self._pool.add_promise(prom)
        return prom

    def put(self, url, **kwargs):
        prom = urlcall.put(url, **kwargs)
        self._pool.add_promise(prom)
        return prom

    @container_wrap
    def head(self, url, **kwargs):
        return urlcall.url_call(url, )

    def add_promise(self, promise: Promise):
        self._pool.add_promise(promise)
