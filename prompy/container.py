import collections
import uuid
import functools

from typing import Dict, Callable

from prompy.promise import Promise


class BasePromiseContainer:
    def add_promise(self, promise: Promise):
        raise NotImplementedError


class BasePromiseRunner(BasePromiseContainer):
    def add_promise(self, promise: Promise):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError


class PromiseContainer(BasePromiseContainer, collections.Container):
    def __init__(self):
        self._promises: Dict[uuid.UUID, Promise] = {}

    def __contains__(self, x: Promise):
        return x.id in self._promises

    def add_promise(self, promise: Promise):
        self._promises[promise.id] = promise


def container_wrap(func: Callable[..., Promise]) -> Callable[..., Promise]:

    @functools.wraps(func)
    def _wrap(self: BasePromiseContainer, *args, **kwargs):
        p = func(self, *args, **kwargs)
        self.add_promise(p)
        return p

    return _wrap
