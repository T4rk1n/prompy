"""Experimental multiprocess promise."""
import time

from prompy.errors import PromiseRejectionError, UnhandledPromiseError
from prompy.promise import Promise, PromiseStarter, PromiseState, ThenCallback, CatchCallback, TPromiseResults

from prompy.function_serializer import serialize_fun, deserialize_fun


class ProcessPromise(Promise):
    """
    Experimental Promise for a multiprocessing backend.
    Should only use for long running functions.

    Closures are not serialized properly, only their values are kept.

    This goes for starter and callbacks:
    * Objects need to be marshal compatible.
    * Need to import any module at function level.

    """
    def __init__(self, starter: PromiseStarter, namespace=None,
                 *args, **kwargs):
        super().__init__(starter, *args, **kwargs)
        self.namespace = namespace
        self._starter = serialize_fun(starter)

    def exec(self):
        try:
            starter = deserialize_fun(self._starter, namespace=self.namespace)
            starter(self.resolve, self.reject)
            self._state = PromiseState.fulfilled
        except Exception as error:
            self.reject(error)
            if self._raise_again:
                raise PromiseRejectionError(f"Promise {self.id} was rejected") from error
        finally:
            self.completed_at = time.time()
            for c in self._complete:
                c(self.result, self._error)

    def then(self, func: ThenCallback):
        self._then.append(serialize_fun(func))
        return self

    def catch(self, func: CatchCallback):
        self._catch.append(serialize_fun(func))
        return self

    def resolve(self, result: TPromiseResults):
        self._result = result
        self._results.append(result)
        for t in self._then:
            then = deserialize_fun(t, self.namespace)
            then(result)

    def reject(self, error: Exception):
        self._error = error
        self._state = PromiseState.rejected
        if not self._catch:
            raise UnhandledPromiseError(f"Unhandled promise exception: {self.id}") from error
        for c in self._catch:
            catch = deserialize_fun(c, self.namespace)
            catch(error)
