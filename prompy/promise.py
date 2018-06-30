"""Promise for python"""
import collections
import enum
import uuid
from typing import Callable, Any, List, Union, Deque, TypeVar, Generic, Tuple

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
        Promise takes at least a starter method with params to this promise
        resolve and reject. Does not call exec by default but with start_now
        the execution will be synchronous.

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
            self.callback_handler(t(result))
        self._finish(PromiseState.fulfilled)

    def reject(self, error: Exception):
        """
        Reject the promise.

        :param error:
        :return:
        """
        self._error = error
        if not self._catch:
            self._state = PromiseState.rejected
            raise UnhandledPromiseError(
                f"Unhandled promise exception: {self.id}") from error
        for c in self._catch:
            self.callback_handler(c(error))
        self._finish(PromiseState.rejected)

    def _finish(self, state):
        for c in self._complete:
            self.callback_handler(c(self.result, self._error))
        self._state = state

    def exec(self):
        """
        Execute the starter method.

        :return:
        """
        try:
            started = self._starter(self.resolve, self.reject)
            self.callback_handler(started)
        except Exception as error:
            self.reject(error)
            if self._raise_again:
                raise PromiseRejectionError(
                    f"Promise {self.id} was rejected") from error

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

    def callback_handler(self, obj: Any):
        """
        Override to handle the return value of callbacks.

        :param obj: The return value of a callback
        :return:
        """
        self._handle_generator_callback(obj)

    # noinspection PyMethodMayBeStatic
    def _handle_generator_callback(self, obj):
        if hasattr(obj, '__iter__') and not hasattr(obj, '__len__'):
            try:
                while True:
                    next(obj)
            except StopIteration:
                pass
