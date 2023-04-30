import atexit
import logging as log
import contextlib

from enum import Enum
from threading import Thread, Event
from datetime import datetime, timedelta
from multiprocessing import Queue


class Holdoff:

    def __init__(self):
        self.deadline = None

    def reset(self, delay=None):
        if delay:
            delay = timedelta(seconds=delay)
        self.deadline = datetime.now()

    @property
    def passed(self):
        return datetime.now() > self.deadline


class ServiceError(Exception):
    pass


class ServiceStoppedError(ServiceError):
    pass


class ServiceSignal(Exception):
    pass


class ServiceRestartSignal(ServiceSignal):
    pass


class RunState(Enum):
    Starting = 2
    Running  = 3
    # Idle     = 4
    Stopping = 5
    Stopped  = 6


class Service(Thread):

    def __init__(self):
        super().__init__()
        self.running = True
        self.deadline = None
        self.state = RunState.Stopped
        self.wanted = False
        self._event = Event()
        self.handlers = []
        self._holdoff = Holdoff()
        atexit.register(self.atexit)
        super().start()

    def atexit(self):
        log.debug(f"{self.name}: Requesting thread exit..")
        self.running = False
        self._event.set()
        self.join()
        log.debug(f"{self.name}: Thread cleanup done")

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

    def shutdown(self):
        if self.state != RunState.Stopped:
            self.stop()
            self.await_stopped()

        self.running = False
        self._event.set()
        return self.join()

    def idle(self, timeout=None):
        if self._event.wait(timeout=timeout):
            self._event.clear()

    def _attempt_start(self):
        try:
            log.debug(f"{self.name} worker start")
            self.worker_start()
        except Exception as E:
            log.exception(f"{self.name}: Failed to start worker: {E}. Retrying in 1 second.")
            self._holdoff.reset(delay=1)
        else:
            log.debug(f"{self.name}: Worker started")
            self.state = RunState.Running

    def _attempt_run(self):
        try:
            self.worker_run(timeout=0.3)
        except Exception:
            log.exception(f"{self.name}: Unexpected exception while running worker")
            log.warning(f"{self.name}: Stopping worker due to exception")
            self._holdoff.reset()
            self.state = RunState.Stopping

    def _attempt_stop(self):
        try:
            self.worker_stop()
        except Exception as E:
            log.exception(f"{self.name}: Failed to stop worker: {E}. Retrying in 1 second.")
            self._holdoff.reset(delay=1)
        else:
            log.debug(f"{self.name}: Worked stopped")
            self.state = RunState.Stopped

    def run(self):
        while self.running:
            if self.state == RunState.Starting:
                if self._holdoff.passed:
                    self._attempt_start()
                else:
                    self.idle(timeout=0.1)

            elif self.state == RunState.Running:
                if self.wanted:
                    self._attempt_run()
                else:
                    log.debug(f"{self.name}: Stopping worker")
                    self._holdoff.reset()
                    self.state = RunState.Stopping

            elif self.state == RunState.Stopping:
                if self._holdoff.passed:
                    self._attempt_stop()
                else:
                    self.idle(timeout=0.1)

            elif self.state == RunState.Stopped:
                if self.wanted:
                    log.debug(f"{self.name}: Starting worker")
                    self._holdoff.reset()
                    self.state = RunState.Starting
                else:
                    self.idle()
            else:
                raise ValueError("Unknown state value")

        log.debug(f"{self.name}: Shutting down thread")
        if self.state == RunState.Running:
            self.worker_stop()
        log.info(f"{self.name}: Thread exit")

    def worker_start(self):
        pass

    def worker_run(self, timeout):
        pass

    def worker_stop(self):
        pass

    def notify(self, data):
        for handler in self.handlers:
            handler(data)

    @contextlib.contextmanager
    def tap(self, handler):
        self.handlers.append(handler)
        try:
            yield self
        finally:
            self.handlers.remove(handler)

    def await_ready(self):
        while True:
            log.debug(f"{self.name}: Awaiting ready ({self.state})")
            if not self.running:
                raise RuntimeError(f"{self.name}: Waiting for stopped thread")

            if self.state == RunState.Running:
                log.debug(f"{self.name}: Ready")
                return True

            self.idle(timeout=0.1)


class ServiceManager:

    def __init__(self):
        self.svcs = {}
        self.refs = {}

    def register(self, name: str, svc: Service):
        if name in self.svcs:
            raise KeyError(f"Trying to register {name!r} as {svc} while already taken by {self.svcs[name]}")

        self.svcs[name] = svc
        self.refs[name] = 0

    def unregister(self, name: str):
        if name not in self.svcs:
            raise KeyError(f"Trying to unregister unknown service {name!r}")

        del self.svcs[name]
        del self.refs[name]

    def get(self, name: str, ready=True) -> Service:
        if name not in self.svcs:
            raise KeyError(f"Requested unknown service {name!r}")

        svc = self.svcs[name]
        self.refs[name] += 1

        if self.refs[name] == 1:
            svc.start()
            if ready:
                svc.await_ready()

        return svc

    def put(self, name: str):
        if name not in self.svcs:
            raise KeyError(f"Requested unknown service {name!r}")

        svc = self.svcs[name]

        assert self.refs[name]

        self.refs[name] -= 1

        if not self.refs[name]:
            svc.stop()

    @contextlib.contextmanager
    def borrow(self, name: str):
        svc = self.get(name)
        try:
            yield svc
        finally:
            self.put(name)

    def stream(self, name: str):
        with self.borrow(name) as svc:
            queue = Queue()

            def handler(data):
                queue.put(data)

            with svc.tap(handler):
                while True:
                    try:
                        yield queue.get()
                    except (EOFError, OSError):
                        break
