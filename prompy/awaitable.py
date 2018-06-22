"""
Promise you can await.

Usage:
```
import asyncio

from prompy.awaitable import AwaitablePromise
from prompy.networkio.urlcall import url_call

async def call_starter(resolve, _):
    google = await url_call('http://www.google.com', prom_type=AwaitablePromise)
    resolve(google)

p = AwaitablePromise(call_starter)

@p.then
def then(result):
    print(result)
    asyncio.get_event_loop().stop()

asyncio.get_event_loop().run_forever()
```
"""
import asyncio

from typing import Any

from prompy.container import BasePromiseRunner
from prompy.errors import UnhandledPromiseError
from prompy.promise import Promise, CompleteCallback, CatchCallback, ThenCallback, PromiseStarter, PromiseState
from prompy.promtools import promise_wrap


class AwaitablePromise(Promise):
    """
    asyncio compatible promise

    Await it to get the result.
    Need a running loop to actually start the executor.
    """

    def __init__(self, starter: PromiseStarter, then: ThenCallback = None, catch: CatchCallback = None,
                 complete: CompleteCallback = None, loop=None):
        super().__init__(starter, then, catch, complete,
                         raise_again=False,
                         start_now=False)
        self.loop = loop or asyncio.get_event_loop()
        self.future: asyncio.Future = self.loop.create_future()
        self.loop.call_soon_threadsafe(self.exec)

    def resolve(self, result: Any):
        self._result = result
        self._results.append(result)
        self.future.set_result(result)

        for t in self._then:
            self._ensure_awaited(t(result))

    def reject(self, error: Exception):
        self._error = error
        self._state = PromiseState.rejected

        if not self._catch:
            # only set exception if no handler, will be thrown back in loop exception_handler
            self.future.set_exception(error)
            raise UnhandledPromiseError(f"Unhandled promise exception: {self.id}") from error

        self.future.set_result(error)

        for catcher in self._catch:
            self._ensure_awaited(catcher(error))

    def finish(self):
        for c in self._complete:
            self._ensure_awaited(c(self.result))

    def __await__(self):
        while not self.future.done():
            yield from self.future
        return self.future.result()

    def _starter_handler(self, started):
        self._ensure_awaited(started)

    def _ensure_awaited(self, obj):
        if asyncio.iscoroutine(obj):
            self.loop.create_task(obj)

    @property
    def error(self):
        """
        :raise: invalid state if the promise was not completed.
        :return: the exception or the handled error
        """
        return self.future.exception() or self._error

    @staticmethod
    def wrap(func):
        return promise_wrap(func, prom_type=AwaitablePromise)


class AsyncPromiseRunner(BasePromiseRunner):
    """Run the loop forever"""

    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def stop(self):
        self.loop.stop()

    def add_promise(self, promise: Promise):
        pass

    def start(self):
        self.loop.run_forever()
