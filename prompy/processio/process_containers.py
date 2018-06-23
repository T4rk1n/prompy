"""Experimental multiprocessing promise containers."""
import multiprocessing
import time
from queue import Empty
from typing import Callable, NamedTuple, List

from prompy.container import BasePromiseContainer, BasePromiseRunner
from prompy.processio.process_promise import ProcessPromise
from prompy.promise import Promise


class ProcessPromiseQueue(BasePromiseContainer):
    """
    A queue for a process promise.

    Usage: `multiprocess.Process(target=ProcessPromiseQueue.run)`
    """
    __queue_index = 0

    def __init__(self,
                 on_idle: Callable = None,
                 max_idle: float = 2,
                 poll_time: float=0.01,
                 error_list: multiprocessing.Queue=None,
                 idle_check: bool=False,
                 raise_again: bool=True):
        """
        Queue initializer.

        :param on_idle: callback to call when the queue is idle
        :param max_idle: max time the queue can be idling.
        :param poll_time: the frequency of queue timeouts.
        :param error_list: a multiprocess container to exchange errors.
        :param idle_check: to use the idle timeout or not.
        :param raise_again: to raise errors again after catch (stop the queue).
        """
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
        """The number of promise still to resolve."""
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
    """A pool of PromiseQueue to add promise to."""
    def __init__(self, pool_size=10, queue_options=None):
        """
        :param pool_size: number of processes that will be spawned.
        :param queue_options: options to give to spawned queue
        """
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
