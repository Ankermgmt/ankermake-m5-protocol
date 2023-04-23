import atexit
import contextlib
import logging as log

from datetime import datetime, timedelta
from enum import Enum
from threading import Thread, Event
from multiprocessing import Queue


class RunState(Enum):
    Starting = 2
    Running  = 3
    # Idle     = 4
    Stopping = 5
    Stopped  = 6


class Service(Thread):

    def __init__(self, idle_timeout=10):
        super().__init__()
        self.timeout = timedelta(seconds=idle_timeout)
        self.running = True
        self.deadline = None
        self.state = RunState.Stopped
        self.wanted = False
        self._event = Event()
        atexit.register(self.atexit)
        super().start()

    def atexit(self):
        log.info(f"{self.name}: Requesting thread exit..")
        self.running = False
        self._event.set()
        self.join()
        log.info(f"{self.name}: Thread cleanup done")

    @property
    def name(self):
        return type(self).__name__

    def start(self):
        log.info(f"{self.name}: Requesting start")
        self.wanted = True
        self._event.set()

    def stop(self):
        log.info(f"{self.name}: Requesting stop")
        self.wanted = False
        self._event.set()

    def run(self):
        holdoff = None

        while self.running:
            if self.state == RunState.Starting:
                log.debug(f"{self.name}: {datetime.now()} vs holdoff {holdoff}")
                if datetime.now() > holdoff:
                    try:
                        log.info(f"{self.name} worker start")
                        self.worker_start()
                    except Exception as E:
                        log.error(f"{self.name}: Failed to start worker: {E}. Retrying in 1 second.")
                        holdoff = datetime.now() + timedelta(seconds=1)
                    else:
                        log.info(f"{self.name}: Worker started")
                        self.state = RunState.Running
                else:
                    self._event.wait(timeout=0.1)
                    self._event.clear()

            elif self.state == RunState.Running:
                if self.wanted:
                    try:
                        self.worker_run(timeout=0.3)
                    except Exception:
                        log.exception("Unexpected exception while running worker")
                        log.warning(f"{self.name}: Stopping worker due to exception")
                        holdoff = datetime.now()
                        self.state = RunState.Stopping
                else:
                    log.info(f"{self.name}: Stopping worker")
                    holdoff = datetime.now()
                    self.state = RunState.Stopping

            elif self.state == RunState.Stopping:
                if datetime.now() > holdoff:
                    try:
                        self.worker_stop()
                    except Exception as E:
                        log.error(f"{self.name}: Failed to stop worker: {E}. Retrying in 1 second.")
                        holdoff = datetime.now() + timedelta(seconds=1)
                    else:
                        log.info(f"{self.name}: Worked stopped")
                        self.state = RunState.Stopped
                else:
                    self._event.wait(timeout=0.1)
                    self._event.clear()

            elif self.state == RunState.Stopped:
                if self.wanted:
                    log.info(f"{self.name}: Starting worker")
                    holdoff = datetime.now()
                    self.state = RunState.Starting
                else:
                    self._event.wait()
                    self._event.clear()
            else:
                raise ValueError("Unknown state value")

        log.info(f"{self.name}: Shutting down thread")
        if self.state == RunState.Running:
            self.worker_stop()
        log.info(f"{self.name}: Thread exit")

    def worker_start(self):
        pass

    def worker_run(self, timeout):
        pass

    def worker_stop(self):
        pass


class QueueTap:

    def __init__(self, queue):
        self.queue = queue

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self.get()
        except (EOFError, OSError):
            raise StopIteration()

    def get(self, timeout=None):
        return self.queue.get(timeout=timeout)


class MultiQueue(Service):

    def __init__(self, idle_timeout=10):
        super().__init__(idle_timeout)
        self.targets = []

    @contextlib.contextmanager
    def tap(self):
        queue = Queue()
        self.add_target(queue)
        try:
            yield QueueTap(queue)
        finally:
            self.del_target(queue)

    def put(self, obj):
        for target in self.targets:
            target.put(obj)

    def add_target(self, target):
        if not self.targets:
            self.start()
        self.targets.append(target)

    def del_target(self, target):
        if target in self.targets:
            self.targets.remove(target)
            if not self.targets:
                self.stop()
