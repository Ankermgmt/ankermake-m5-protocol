import atexit
import logging as log
import contextlib

from enum import Enum
from threading import Thread, Event
from datetime import datetime, timedelta
from multiprocessing import Queue
from queue import Empty


class Holdoff:

    def __init__(self):
        self.deadline = None

    def reset(self, delay=None):
        self.deadline = datetime.now()
        if delay:
            self.deadline += timedelta(seconds=delay)

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
        self.daemon = True
        super().start()

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

    def restart(self):
        log.info(f"{self.name}: Requesting restart")
        wanted = self.wanted
        self.stop()
        self.await_stopped()
        if wanted:
            self.start()
            self.await_ready()

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
            log.debug(f"{self.name} worker starting..")
            self.worker_start()
        except Exception as E:
            if self.wanted:
                if isinstance(E, TimeoutError):
                    pass
                elif isinstance(E, ServiceStoppedError):
                    log.error(f"{self.name}: Failed to start worker: {E}. Retrying in 1 second.")
                else:
                    log.exception(f"{self.name}: Failed to start worker: {E}. Retrying in 1 second.")
                self._holdoff.reset(delay=1)
            else:
                if not isinstance(E, (TimeoutError, ServiceStoppedError)):
                    log.error(f"{self.name}: Failed to start worker: {E}. Shutting down service.")
                self.state = RunState.Stopped
        else:
            log.info(f"{self.name}: Worker started")
            self.state = RunState.Running

    def _attempt_run(self):
        try:
            self.worker_run(timeout=0.1)
        except ServiceRestartSignal:
            log.info(f"{self.name}: Service requested restart.")
            self._holdoff.reset(delay=1)
            self.state = RunState.Stopping
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
            log.info(f"{self.name}: Worker stopped")
            self.state = RunState.Stopped

    def run(self):
        self.worker_init()

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
                    self.idle(timeout=0.1)
            else:
                raise ValueError("Unknown state value")

        log.debug(f"{self.name}: Shutting down thread")
        if self.state == RunState.Running:
            self.handlers.clear()
            self.worker_stop()
        log.debug(f"{self.name}: Thread exit")

    def worker_init(self):
        pass

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
            if not (self.running and self.wanted):
                raise ServiceStoppedError(f"{self.name}: Waiting for stopped thread")

            if self.state == RunState.Running:
                log.debug(f"{self.name}: Ready")
                return True

            self.idle(timeout=0.4)

    def await_stopped(self):
        while True:
            if self.wanted:
                log.warning(f"{self.name}: Service started while waiting for it to stop")
                return False

            if self.state == RunState.Stopped:
                log.debug(f"{self.name}: Stopped")
                return True

            self.idle(timeout=0.4)


class ServiceManager:

    def __init__(self):
        self.svcs = {}
        self.refs = {}
        atexit.register(self.atexit)

    def __iter__(self):
        return iter(self.svcs)

    def __contains__(self, name):
        return name in self.svcs

    def atexit(self):
        log.debug("ServiceManager: Shutting down threads..")
        self.dump()
        for svc in self.svcs.values():
            if svc.state != RunState.Stopped:
                svc.stop()

        log.debug("ServiceManager: Waiting for threads to stop..")
        self.dump()
        for svc in self.svcs.values():
            svc.await_stopped()

        log.debug("ServiceManager: Cleaning up threads..")
        self.dump()
        for svc in self.svcs.values():
            svc.shutdown()

        log.info("ServiceManager: Shutdown complete")

    def dump(self):
        log.debug("Service state")
        for name in self.svcs:
            svc = self.svcs[name]
            ref = self.refs[name]
            log.debug(f"  [{ref:>4}] {name:20} running={svc.running} state={svc.state} wanted={svc.wanted}")

    def register(self, name: str, svc: Service):
        if name in self:
            raise KeyError(f"Trying to register {name!r} as {svc} while already taken by {self.svcs[name]}")

        self.svcs[name] = svc
        self.refs[name] = 0

    def unregister(self, name: str):
        if name not in self:
            raise KeyError(f"Trying to unregister unknown service {name!r}")

        if self.refs[name]:
            raise ServiceError(f"Trying to unregister service {name!r} with {self.refs[name]} reference(s)")

        del self.svcs[name]
        del self.refs[name]

    def restart_all(self, await_ready=True):
        wanted = {}

        for name, svc in self.svcs.items():
            wanted[name] = svc.wanted
            svc.stop()

        for name, svc in self.svcs.items():
            svc.await_stopped()

        for name, svc in self.svcs.items():
            if not wanted[name]:
                continue

            svc.start()

            if not await_ready:
                continue

            try:
                svc.await_ready()
            except ServiceStoppedError:
                # ignore service stopped error, since restart_all() is a
                # best-effort function.
                pass

    def get(self, name: str, ready=True) -> Service:
        if name not in self:
            raise KeyError(f"Requested unknown service {name!r}")

        svc = self.svcs[name]
        self.refs[name] += 1

        if self.refs[name] == 1:
            svc.start()

        if ready:
            try:
                svc.await_ready()
            except ServiceError:
                self.put(name)
                raise

        return svc

    def put(self, name: str):
        if name not in self:
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

    def stream(self, name: str, timeout: float=None):
        try:
            with self.borrow(name) as svc:
                queue = Queue()

                with svc.tap(lambda data: queue.put(data)):
                    while svc.state == RunState.Running:
                        yield queue.get(timeout=timeout)
        except (EOFError, OSError, ServiceStoppedError, Empty):
            return
