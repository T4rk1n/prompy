"""Promise for python"""
import collections
import enum
import uuid
from typing import Callable, Any, List, Union, Deque, TypeVar, Generic, Tuple

import time

from prompy.errors import UnhandledPromiseError, PromiseRejectionError

TPromiseResults = TypeVar('PromiseReturnType')

# generics don't work with callbacks, check result prop for type.
CompleteCallback = Callable[[Union[List[TPromiseResults], TPromiseResults], Exception], None]
ThenCallback = Callable[[TPromiseResults], None]
CatchCallback = Callable[[Exception], None]

PromiseStarter = Callable[[Callable, Callable], None]


class PromiseState(enum.Enum):
    pending = 1
    fulfilled = 2
    rejected = 3


class Promise(Generic[TPromiseResults]):
    """
    Promise interface
    Based on js Promises.

    Basic usage:

    `p = Promise(lambda resolve, reject: resolve('Hello')).then(print)`
    """

    def __init__(self, starter: PromiseStarter,
                 then: ThenCallback=None,
                 catch: CatchCallback=None,
                 complete: CompleteCallback=None,
                 raise_again: bool=False,
                 start_now: bool=False,
                 results_buffer_size: int = 100):
        """
        Promise takes at least a starter method with params to this promise resolve and reject.
        Does not call exec by default but with start_now the execution will be synchronous.

        :param starter: otherwise known as executor.
        :param then: initial resolve callback
        :param catch: initial catch callback
        :param complete: initial complete callback
        :param raise_again: raise the rejection error again.
        :param start_now:
        :param results_buffer_size: number of results to keep in the buffer.
        """
        self.canceled = False
        self.completed_at = None
        self._promise_id: uuid.UUID = uuid.uuid4()
        self._then: List[ThenCallback] = [then] if then else []
        self._catch: List[CatchCallback] = [catch] if catch else []
        self._complete: List[CompleteCallback] = [complete] if complete else []
        self._rejected = False
        self._completed = False
        self._raise_again = raise_again
        self._starter = starter
        self._result: Any = None
        self._results: Deque = collections.deque(maxlen=results_buffer_size)
        self._error: Exception = None
        self._state = PromiseState.pending
        if start_now:
            self.exec()

    def then(self, func: ThenCallback):
        """
        Add a callback to resolve

        :param func: callback to resolve
        :return:
        """
        self._then.append(func)
        if self.state == PromiseState.fulfilled:
            func(self.result)
        return self

    def catch(self, func: CatchCallback):
        """
        Add a callback to rejection

        :param func:
        :return:
        """
        self._catch.append(func)
        if self.state == PromiseState.rejected:
            func(self.error)
        return self

    def complete(self, func: CompleteCallback):
        """
        Add a callback to finally block

        :param func:
        :return:
        """
        self._complete.append(func)
        return self

    def resolve(self, result: TPromiseResults):
        """
        Resolve the promise, called by executor.

        :param result:
        :return:
        """
        self._result = result  # result always the last resolved
        self._results.append(result)
        for t in self._then:
            t(result)

    def reject(self, error: Exception):
        """
        Reject the promise.

        :param error:
        :return:
        """
        self._error = error
        self._state = PromiseState.rejected
        if not self._catch:
            raise UnhandledPromiseError(f"Unhandled promise exception: {self.id}") from error
        for c in self._catch:
            c(error)

    def finish(self):
        for c in self._complete:
            c(self.result, self._error)

    def exec(self):
        """
        Execute the starter method.

        :return:
        """
        try:
            started = self._starter(self.resolve, self.reject)
            self._starter_handler(started)
            self._state = PromiseState.fulfilled
        except Exception as error:
            self.reject(error)
            if self._raise_again:
                raise PromiseRejectionError(f"Promise {self.id} was rejected") from error
        finally:
            self.completed_at = time.time()
            self.finish()

    def _starter_handler(self, started):
        """Override to handle the return value of the starter callback."""
        # handle a generator.
        if hasattr(started, '__iter__') and not hasattr(started, '__len__'):
            try:
                while next(started):
                    pass
            except StopIteration:
                pass

    @property
    def id(self) -> uuid.UUID:
        return self._promise_id

    @property
    def result(self) -> Union[Tuple[TPromiseResults], TPromiseResults]:
        return tuple(self._results) if len(self._results) > 1 else self._result

    @property
    def error(self) -> Exception:
        return self._error

    @property
    def state(self) -> PromiseState:
        return self._state
