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
    Closures are not serialized properly, only their values are kept.
    They also have to be completely marshallable.
    """
    def __init__(self, starter: PromiseStarter, namespace=None, *args, **kwargs):
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
    __queue_index = 0

    def __init__(self,  on_idle: Callable=None, max_idle: float=2, poll_time=0.01):
        self._index = self.__queue_index
        self.__queue_index += 1
        self.max_idle = max_idle
        self.poll_time = poll_time
        self._queue: multiprocessing.Queue = multiprocessing.Queue()
        self._on_idle: Callable = on_idle
        self._running = False

    def add_promise(self, promise: ProcessPromise):
        self._queue.put(promise)

    def run(self):
        idle_start = None
        self._running = True

        while True:
            try:
                current: Promise = self._queue.get()
                current.exec()
                idle_start = None
            except Empty:
                if not idle_start:
                    idle_start = time.time()
                else:
                    idle_time = time.time() - idle_start
                    if idle_time > self.poll_time:
                        if self._on_idle:
                            stop = self._on_idle()
                            if stop:
                                self._running = False
                                return
                        else:
                            self._running = False
                            return

    @property
    def id(self) -> int:
        return self._index


    @property
    def running(self):
        return self._running


class _ProcessingQueue(NamedTuple):
    process_id: int
    process: multiprocessing.Process
    queue: ProcessPromiseQueue


class PromiseProcessPool(BasePromiseRunner):
    def start(self):
        pass

    def __init__(self, pool_size=10, populate=False):
        self._process_index = 0
        self._next_process_id = 0
        self._pool = multiprocessing.Pool(processes=pool_size)
        self._processes: List[_ProcessingQueue] = []
        self._responses = []
        self._pool_size = pool_size
        if populate:
            self.populate()

    def add_promise(self, promise: ProcessPromise):
        q = self._processes[self._process_index]
        self._process_index += 1
        if self._process_index >= self._pool_size:
            self._process_index = 0
        q.queue.add_promise(promise)

    def add_queue(self):
        queue = ProcessPromiseQueue()
        p = multiprocessing.Process(target=queue.run, )
        p.start()
        self._processes.append(_ProcessingQueue(self._next_process_id, p, queue))
        self._next_process_id += 1

    def populate(self, ):
        while len(self._processes) < self._pool_size:
            self.add_queue()

    def running(self):
        return all([x.queue.running for x in self._processes])

    def stop(self):
        for proc in self._processes:
            proc.process.terminate()
            proc.process.join()
