import collections
import uuid
import functools

from typing import Dict, Callable, List

from prompy.promise import Promise


class BasePromiseContainer:
    """Interface for a promise container."""
    def add_promise(self, promise: Promise):
        """
        Add a promise to the container.

        :param promise:
        :return:
        """
        raise NotImplementedError

    def add_promises(self, *promises: Promise):
        """
        Add all the promises.

        :param promises: promises to add
        :return:
        """
        for promise in promises:
            self.add_promise(promise)


class BasePromiseRunner(BasePromiseContainer):
    """A container that need to start and stop."""
    def add_promise(self, promise: Promise):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError


class PromiseContainer(BasePromiseContainer, collections.Container):
    """
    Basic promise container.

    Keeps the promises in a dict with the promise id as key.
    """
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
