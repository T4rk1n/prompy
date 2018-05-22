import asyncio

from typing import Any

from prompy.container import BasePromiseRunner
from prompy.promise import Promise, CompleteCallback, CatchCallback, ThenCallback, PromiseStarter
from prompy.promtools import promise_wrap


class AwaitablePromise(Promise):

    def __init__(self, starter: PromiseStarter, then: ThenCallback = None, catch: CatchCallback = None,
                 complete: CompleteCallback = None, raise_again=False):
        super().__init__(starter, then, catch, complete, raise_again, start_now=False)
        self.loop = asyncio.get_event_loop()
        self.future: asyncio.Future = self.loop.create_future()
        self.loop.call_soon_threadsafe(self.exec)

    def resolve(self, result: Any):
        super(AwaitablePromise, self).resolve(result)
        self.future.set_result(result)

    def reject(self, error: Exception):
        self.future.set_exception(error)
        return super().reject(error)

    def __await__(self):
        while not self.future.done():
            yield from self.future
        return self.future.result()

    @staticmethod
    def wrap(func):
        return promise_wrap(func, prom_type=AwaitablePromise)


class AsyncPromiseRunner(BasePromiseRunner):
    """Run the loop forever"""
    def add_promise(self, promise: Promise):
        pass

    def start(self):
        loop = asyncio.get_event_loop()
        loop.run_forever()
