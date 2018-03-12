import functools
from typing import Callable

import time

from prompy.promise import Promise, PromiseState


def promise_wrap(func, prom_type=Promise, **kw) -> Callable[..., Promise]:
    """Wraps a function return in a promise resolve."""

    @functools.wraps(func)
    def _wrap(*args, **kwargs) -> Promise:
        def _prom(resolve, reject):
            try:
                resolve(func(*args, **kwargs))
            except Exception as error:
                reject(error)
        return prom_type(_prom, **kw)

    return _wrap


class _AllPromiseWrap:

    def __init__(self, promises):
        self.promises = promises
        self.num_promises = len(promises)
        self.res = 0
        self.rejected = False
        self.results = []
        self.rejection = []
        self._resolve = None
        self._reject = None

    def __call__(self, resolve, reject):
        self._resolve = resolve
        self._reject = reject
        if not self.rejected and self.num_promises == self.res:
            resolve(self.results)
        elif sum((1 for x in self.promises if x.state == PromiseState.fulfilled)) == self.num_promises:
            resolve([p.result for p in self.promises])
        elif self.rejected or sum((1 for x in self.promises if x.state == PromiseState.rejected)) > 0:
            reject(Exception("Promise all reject"))

    def then(self, result):
        self.res += 1
        if not self.rejected:
            self.results.append(result)
            if self.res == self.num_promises and self._resolve:
                self._resolve(self.results)

    def catch(self, err):
        self.rejected = True
        if self._reject:
            self._reject(err)


def pall(*promises, prom_type=Promise, **kwargs) -> Promise:
    """Wrap all the promises in a single one that resolve when all promises are done."""
    starter = _AllPromiseWrap(promises)

    for p in promises:
        p.then(starter.then).catch(starter.catch)

    return prom_type(starter, **kwargs)


def piter(iterable, func, prom_type=Promise, **kwargs) -> Promise:
    def starter(resolve, _):
        for i in iterable:
            resolve(func(i))

    return prom_type(starter, **kwargs)


def later(func, delay, wait_func=time.sleep, prom_type=Promise, **kwargs) -> Callable[..., Promise]:
    """Bad, do not use."""

    @functools.wraps(func)
    def _wrap(*args, **kw):

        def starter(resolve, reject):
            wait_func(delay)
            try:
                resolve(func(*args, **kw))
            except Exception as err:
                reject(err)
        return prom_type(starter, **kwargs)

    return _wrap

