import uuid
from typing import Callable, Any, List

import time

from prompy.errors import UnhandledPromiseError

CompleteCallback = Callable[[Any, Exception], None]
ThenCallback = Callable[[Any], None]
CatchCallback = Callable[[Exception], None]

PromiseStarter = Callable[[Callable, Callable], None]


class Promise:
    """ES6-like Promise"""

    def __init__(self, starter: PromiseStarter,
                 then: ThenCallback=None,
                 catch: CatchCallback=None,
                 complete: CompleteCallback=None,
                 raise_again=False, start_now=False):
        self._promise_id: uuid.UUID = uuid.uuid4()
        # TODO refactor callbacks to recursive queues
        self._then: List[Callable] = [then] if then else []
        self._catch: List[Callable] = [catch] if catch else []
        self._complete: List[Callable] = [complete] if complete else []
        self._rejected = False
        self._completed = False
        self._raise_again = raise_again
        self._starter = starter
        self._result: Any = None
        self._error: Exception = None
        self._resolved = False

        self.canceled = False
        self.completed_at = None
        if start_now:
            self.exec()

    @property
    def id(self) -> uuid.UUID:
        return self._promise_id

    def then(self, func: ThenCallback):
        self._then.append(func)
        return self

    def catch(self, func: CatchCallback):
        self._catch.append(func)
        return self

    def complete(self, func: CompleteCallback):
        self._complete.append(func)
        return self

    def resolve(self, result: Any):
        self._resolved = True
        self._result = result
        for t in self._then:
            t(result)

    def reject(self, error: Exception):
        self._error = error
        if not self._catch:
            raise UnhandledPromiseError(f"Unhandled promise exception: {self.id}") from error
        for c in self._catch:
            c(error)

    def exec(self):
        """Wrap this with your fav async method."""
        try:
            self._starter(self.resolve, self.reject)
        except Exception as error:
            self.reject(error)
            if self._raise_again:
                raise
        finally:
            self.completed_at = time.time()
            for c in self._complete:
                c(self._result, self._error)

    @property
    def result(self) -> Any:
        return self._result

    @property
    def error(self) -> Exception:
        return self._error

    @property
    def resolved(self):
        return self._resolved

