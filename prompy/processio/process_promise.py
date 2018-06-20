"""Experimental multiprocess promise and containers."""
import multiprocessing
import time

from typing import NamedTuple, Callable, List
from queue import Empty

from prompy.container import BasePromiseContainer, BasePromiseRunner
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


class ProcessPromiseQueue(BasePromiseContainer):
    """
    A queue for a process promise.
    Usage: `multiprocess.Process(target=ProcessPromiseQueue.run)`
    """
    __queue_index = 0

    def __init__(self,
                 on_idle: Callable = None,
                 max_idle: float = 2,
                 poll_time=0.01,
                 error_list=None,
                 idle_check=False,
                 raise_again=True):
        self._index = self.__queue_index
        self.__queue_index += 1
        self.max_idle = max_idle
        self.poll_time = poll_time
        self._queue: multiprocessing.Queue = multiprocessing.Queue()
        self._on_idle: Callable = on_idle
        self._running = False
        self._errors = []
        self._raise_again = raise_again
        self._idle_check = idle_check
        self._error_list = error_list

    def add_promise(self, promise: ProcessPromise):
        self._queue.put(promise)

    def run(self):
        idle_start = None
        self._running = True

        while True:
            try:
                current: Promise = self._queue.get(timeout=self.poll_time)
                current.exec()
                idle_start = None
            except Empty:
                if not self._idle_check:
                    continue
                if not idle_start:
                    idle_start = time.time()
                else:
                    idle_time = time.time() - idle_start
                    if idle_time > self.max_idle:
                        if self._on_idle:
                            stop = self._on_idle()
                            if stop:
                                self._running = False
                                return
                        else:
                            self._running = False
                            return
            except Exception as e:
                self._errors.append(e)
                if self._error_list:
                    self._error_list.put(e)
                if self._raise_again:
                    self._running = False
                    raise

    @property
    def id(self) -> int:
        return self._index

    @property
    def num_tasks(self) -> int:
        return self._queue.qsize()

    @property
    def running(self):
        return self._running

    @property
    def errors(self):
        return tuple(self._errors)


class _ProcessingQueue(NamedTuple):
    process_id: int
    process: multiprocessing.Process
    queue: ProcessPromiseQueue


class PromiseProcessPool(BasePromiseRunner):
    """
    A pool of PromiseQueue to add promise to.
    """
    def __init__(self, pool_size=10, queue_options=None):
        self._process_index = 0
        self._next_process_id = 0
        self._processes: List[_ProcessingQueue] = []
        self._pool_size = pool_size
        self._started = False
        self._error_list = multiprocessing.Queue()
        self._queue_options = queue_options or {}
        while len(self._processes) < self._pool_size:
            self._add_queue()

    def add_promise(self, promise: ProcessPromise):
        q = self._processes[self._process_index]
        self._process_index += 1
        if self._process_index >= self._pool_size:
            self._process_index = 0
        # TODO verify the queue is running else restart the queue
        q.queue.add_promise(promise)
        if not self._started:
            self.start()

    def _add_queue(self):
        queue = ProcessPromiseQueue(error_list=self._error_list, **self._queue_options)
        p = multiprocessing.Process(target=queue.run, )
        self._processes.append(_ProcessingQueue(self._next_process_id, p, queue))
        self._next_process_id += 1

    def start(self):
        for proc in self._processes:
            proc.process.start()
        self._started = True

    def stop(self):
        for proc in self._processes:
            proc.process.terminate()
            proc.process.join()

    def get_errors(self):
        """Get all the errors from processes, they are consumed."""
        while self._error_list.qsize():
            yield self._error_list.get()

    @property
    def num_tasks(self):
        """Sum of all tasks still in queue."""
        return sum([x.queue.num_tasks for x in self._processes])
