import multiprocessing
import time
from typing import NamedTuple, Callable
from queue import Empty

from prompy.container import PromiseContainer, BasePromiseContainer
from prompy.promise import Promise, PromiseStarter


class ProcessPromise(Promise):
    def __init__(self, starter: PromiseStarter, *args, **kwargs):
        super().__init__(starter, *args, **kwargs)
        self.parent_conn = None
        self.child_conn = None


class ProcessPromiseQueue(BasePromiseContainer):
    __queue_index = 0

    def __init__(self, on_idle: Callable=None, max_idle: float=10, poll_time=0.01):
        self._index = self.__queue_index
        self.__queue_index += 1
        self.max_idle = max_idle
        self.poll_time = poll_time
        self._queue: multiprocessing.Queue = multiprocessing.Queue()
        self._on_idle: Callable = on_idle
        self._running = False

    def _then(self, func):
        pass

    def _catch(self, func):
        pass

    def add_promise(self, promise: Promise):
        self._queue.put(promise)

    def run(self, pipe_back):
        idle_start = None

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
                                return
                        else:
                            return

    @property
    def id(self) -> int:
        return self._index


class _ProcessedQueue(NamedTuple):
    process_id: int
    process: multiprocessing.Process
    queue: ProcessPromiseQueue


class PromiseProcessPool(BasePromiseContainer):
    def __init__(self, pool_len=10):
        self._process_index = 0
        self._next_process_id = 0
        self._processes = []
        self._pool_len = pool_len
        self._parent_pipe, self._child_pipe = multiprocessing.Pipe()

    def add_promise(self, promise: Promise):
        q = self._processes[self._process_index]
        self._process_index += 1
        if self._process_index >= self._pool_len:
            self._process_index = 0

    def add_queue(self):
        queue = ProcessPromiseQueue()
        p = multiprocessing.Process(target=queue.run, )
        p.start()
        self._processes.append(_ProcessedQueue(self._next_process_id, p, queue))
        self._next_process_id += 1


    def populate(self, ):
        pass

    def stop(self):
        for proc in self._processes:
            pass


def test_pipes(pipe):
    import time
    started = time.time()
    while True:
        msg = pipe.poll(0.1)
        if msg:
            m = pipe.recv()
            pipe.send(f"You said: {m}")

        if time.time() - started > 5:
            pipe.send("Timeout")
            return


def test_queue(queue: multiprocessing.Queue):
    import time
    started = time.time()
    while True:
        try:
            msg = queue.get(timeout=0.02)
            if time.time() - started > 2:
                return
        except Exception as e:
            print(e)


def test_1():
    parent, child = multiprocessing.Pipe(duplex=True)
    p = multiprocessing.Process(target=test_pipes, args=(child,))
    p.start()
    started = time.time()
    i = 2
    while True:
        if time.time() - started > 2:
            break
        parent.send(i)
        msg = parent.poll(0.1)
        i += 1
        if msg:
            print(parent.recv())
    p.join()


def test_2():
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=test_queue, args=(q,))
    p.start()
    i = 2
    started = time.time()
    while True:
        if time.time() - started > 3:
            break
        if i % 2 == 0:
            q.put(f'msg-{i}')
        time.sleep(0.3)
        i += 1

if __name__ == '__main__':
    test_2()
