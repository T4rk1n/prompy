"""
Promise you can await.

:Example:

.. code-block:: python

    import asyncio

    from prompy.awaitable import AwaitablePromise
    from prompy.networkio.async_call import call

    async def call_starter(resolve, _):
        google = await call('http://www.google.com')
        resolve(google)

    p = AwaitablePromise(call_starter)

    @p.then
    def then(result):
        print(result)
        asyncio.get_event_loop().stop()

    @p.catch
    def catch(err):
        asyncio.get_event_loop().stop()
        raise err

    asyncio.get_event_loop().run_forever()

"""
import asyncio

from typing import Any

from prompy.container import BasePromiseRunner
from prompy.errors import UnhandledPromiseError
from prompy.promise import Promise, CompleteCallback,\
    CatchCallback, ThenCallback, PromiseStarter, PromiseState
from prompy.promtools import promise_wrap


class AwaitablePromise(Promise):
    """
    asyncio compatible promise

    Await it to get the result.
    Need a running loop to actually start the executor.
    """

    def __init__(self, starter: PromiseStarter,
                 then: ThenCallback = None,
                 catch: CatchCallback = None,
                 complete: CompleteCallback = None,
                 loop: asyncio.AbstractEventLoop=None):
        super().__init__(starter, then, catch, complete,
                         raise_again=False,
                         start_now=False)
        self.loop = loop or asyncio.get_event_loop()
        self.future: asyncio.Future = self.loop.create_future()
        self.loop.call_soon_threadsafe(self.exec)

    def resolve(self, result: Any):
        self._result = result
        self._results.append(result)

        if not self._then:
            return self._finish(PromiseState.fulfilled)

        for t in self._then:
            self._ensure_awaited(t(result),
                                 callback=self._done(
                                     self._finish,
                                     PromiseState.fulfilled,
                                     len(self._then)))

    def reject(self, error: Exception):
        self._error = error

        if not self._catch:
            self._state = PromiseState.rejected
            raise UnhandledPromiseError(
                f"Unhandled promise exception: {self.id}") from error

        for catcher in self._catch:
            self._ensure_awaited(catcher(error),
                                 callback=self._done(
                                     self._finish,
                                     PromiseState.fulfilled,
                                     len(self._catch)))

    def _finish(self, state):
        if not self._complete:
            self._on_complete(state)

        for c in self._complete:
            self._ensure_awaited(c(self.result, self._error),
                                 callback=self._done(
                                     self._on_complete,
                                     state,
                                     len(self._complete)))

    def _on_complete(self, state):
        if self._error:
            self.future.set_exception(self._error)
        else:
            self.future.set_result(self.result)
        self._state = state

    def _done(self, on_finish, state, to_do):
        done = asyncio.Queue(loop=self.loop)

        def _done(*args, **kwargs):
            done.put_nowait(1)
            if done.qsize() == to_do:
                on_finish(state)

        return _done

    def __await__(self):
        while not self.future.done():
            yield from self.future
        return self.future.result()

    def callback_handler(self, obj: Any):
        self._ensure_awaited(obj)

    def _ensure_awaited(self, obj, callback=None):
        if asyncio.iscoroutine(obj):
            task = self.loop.create_task(obj)
            if callback:
                task.add_done_callback(callback)
        elif callback:
            callback()

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
