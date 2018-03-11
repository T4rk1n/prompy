import queue
import threading
import uuid
from typing import Callable, Dict

import time

from prompy.promise import Promise


class PromiseQueue:
    __thread_index = 0

    def __init__(self, start=False, max_idle=10, on_stop: Callable = None, queue_timeout=0.01, interval=0.01):
        self.index = PromiseQueue.__thread_index
        self._thread = threading.Thread(target=self._run, name=f"PromiseQueue-{self.index}")
        PromiseQueue.__thread_index += 1
        self._queue = queue.Queue()
        self._promises: Dict[uuid.UUID, Promise] = {}
        self._lock: threading.Lock = threading.Lock()
        self._stop_event = threading.Event()
        self._running = False
        self._idle_time = 0
        self._max_idle = max_idle
        self._started = False
        self._on_stop = on_stop
        self._queue_timeout = queue_timeout
        self._interval = interval
        self._error = None
        if start:
            self.start()

    def add(self, promise: Promise):
        self._promises[promise.id] = promise
        self._queue.put(promise.id)

    def _run(self):
        self._running = True
        idle_start = None
        while self._running:
            try:
                current = self._queue.get(block=False, timeout=self._queue_timeout)
                idle_start = None
                promise = self._promises[current]
                self._lock.acquire()
                if not promise.canceled:
                    promise.exec()
                    del self._promises[current]
                self._lock.release()
                self._stop_event.wait(self._interval)
                if self._stop_event.is_set():
                    self._running = False
            except queue.Empty:
                if not idle_start:
                    idle_start = time.time()
                else:
                    idle_time = time.time() - idle_start
                    if idle_time > self._max_idle:
                        self._running = False
            except Exception as e:
                self._running = False
                self._error = e
                self._stopped()
                raise e
        self._stopped()

    def start(self):
        if not self._started:
            self._thread.start()
            self._started = True

    def cancel(self, cancel_id: uuid.UUID):
        prom = self._promises.get(cancel_id)
        if prom and not prom.canceled:
            prom.canceled = True

    def stop(self):
        self._stop_event.set()

    @property
    def running(self):
        return self._running

    @property
    def error(self):
        return self._error

    def _stopped(self):
        if self._on_stop:
            self._on_stop(self)


class PromiseQueuePool:
    def __init__(self, pool_size=8, start=False, max_idle=2):
        self._max_idle = max_idle
        self.pool_size = pool_size
        self._pool = queue.Queue(maxsize=pool_size)
        self._on_thread_stop = None
        if start:
            self.populate()

    def add_promise(self, promise: Promise):
        if self._pool.qsize() < self.pool_size:
            self._add_queue()
        while True:
            pq = self._pool.get()
            if not pq.running:
                self._add_queue()
            else:
                pq.add(promise)
                self._pool.put(pq)
                return

    def _add_queue(self):
        pq = PromiseQueue(start=True, max_idle=self._max_idle, on_stop=self._thread_stopped)
        self._pool.put(pq)

    def stop(self):
        while True:
            try:
                pq = self._pool.get()
                pq.stop()
            except queue.Empty:
                break

    def populate(self):
        while self._pool.qsize() < self.pool_size:
            try:
                self._add_queue()
            except queue.Full:
                return

    def is_running(self):
        running = []
        while True:
            try:
                pq = self._pool.get_nowait()
                if pq.running:
                    running.append(pq)
            except queue.Empty:
                break

        is_running = len(running) > 0
        for r in running:
            self._pool.put_nowait(r)

        return is_running

    def on_thread_stop(self, func):
        self._on_thread_stop = func

    def _thread_stopped(self, t):
        if self._on_thread_stop:
            self._on_thread_stop(t)

