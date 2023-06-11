import sys
import atexit
import logging
import contextlib

from enum import Enum
from threading import Thread, Event
from datetime import datetime, timedelta
from multiprocessing import Queue

from ..lib import trace


class Holdoff:
    """Holdoff manages a deadline, set some time in the future.

    When creating a new Holdoff object, its deadline is initially set to
    datetime.now().

    h = Holdoff()

    # set a deadline for 0.5 seconds from now
    h.reset(delay=0.5)

    # will be slightly less than 0.5
    print(h.remaining)

    print(h.passed) # False
    time.sleep(1)
    print(h.passed) # True
    """

    def __init__(self):
        self.deadline = datetime.now()

    def __repr__(self):
        return f"{self.__class__.__name__}<deadline={self.deadline}, remaining={self.remaining}>"

    def reset(self, delay=None):
        self.deadline = datetime.now()
        if delay:
            self.deadline += timedelta(seconds=delay)

    @property
    def remaining(self):
        return (self.deadline - datetime.now()).total_seconds()

    @property
    def passed(self):
        return self.remaining < 0


class WaitableHoldoff(Holdoff):

    def __init__(self):
        super().__init__()
        self._event = Event()

    def wait(self):
        rem = self.remaining
        if rem < 0:
            self._event.clear()
            return True

        if self._event.wait(rem):
            self._event.clear()
            return self.passed
        else:
            return True

    def signal(self):
        self._event.set()


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
    Idle     = 4
    Stopping = 5
    Stopped  = 6


class Service(Thread):

    def __init__(self, app):
        super().__init__()
        self._log = logging.getLogger(type(self).__name__)
        self.running = True
        self.deadline = None
        self._state = RunState.Stopped
        self.wanted = False
        self._event = WaitableHoldoff()
        self.handlers = []
        self.daemon = True
        self.app = app
        self._shutdown = False
        self.name = type(self).__name__
        super().start()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new):
        # self._log.debug(f"Changing state [{self._state.name}] -> [{new.name}]")
        self._state = new

    def start(self):
        self._log.info("Requesting start")
        self.wanted = True
        self._event.signal()

    def stop(self):
        self._log.info("Requesting stop")
        self.wanted = False
        if self._shutdown:
            self._event.reset()
        self._event.signal()

    def restart(self):
        self._log.info("Requesting restart")
        wanted = self.wanted
        self.stop()
        self.await_stopped()
        if wanted:
            self.start()
            self.await_ready()

    def shutdown(self):
        self._shutdown = True

        if self.state != RunState.Stopped:
            self.stop()
            self.await_stopped()

        self.running = False
        self._event.signal()
        return self.join()

    def idle(self, timeout=None):
        if timeout:
            self._event.reset(delay=timeout)
        return self._event.wait()

    def _attempt_start(self):
        try:
            self._log.debug(f"{self.name} worker starting..")
            self.worker_start()
        except Exception as E:
            if self.wanted:
                if isinstance(E, TimeoutError):
                    pass
                elif isinstance(E, ServiceStoppedError):
                    self._log.error(f"Failed to start worker: {E}. Retrying in 1 second.")
                else:
                    self._log.exception(f"Failed to start worker: {E}. Retrying in 1 second.")
                self._event.reset(delay=1)
            else:
                if not isinstance(E, (TimeoutError, ServiceStoppedError)):
                    self._log.error(f"Failed to start worker: {E}. Shutting down service.")
                self.state = RunState.Stopped
        else:
            self._log.info("Worker started")
            self.state = RunState.Running

    def _attempt_run(self):
        try:
            self._event.reset(delay=0.1)
            self.worker_run(timeout=0.1)
        except ServiceRestartSignal:
            self._log.info("Service requested restart.")
            self.state = RunState.Stopping
            self._event.reset(delay=1)
        except Exception:
            self._log.exception("Unexpected exception while running worker")
            self._log.warning("Stopping worker due to exception")
            self.state = RunState.Stopping
            self._event.reset()

    def _attempt_stop(self):
        try:
            self.worker_stop()
        except Exception as E:
            self._log.exception(f"Failed to stop worker: {E}. Retrying in 1 second.")
            self._event.reset(delay=1)
        else:
            self._log.info("Worker stopped")
            self.state = RunState.Stopped

    def run(self):
        self.worker_init()

        while self.running:
            match self.state:
                case RunState.Starting:
                    if self._event.wait():
                        self._attempt_start()
                    else:
                        self._event.reset(delay=1)

                case RunState.Running:
                    if self.wanted:
                        self._attempt_run()
                    elif not self._shutdown:
                        self._log.debug("Worker going idle")
                        self.state = RunState.Idle
                        self._event.reset(delay=5)

                case RunState.Idle:
                    if self._shutdown or self._event.wait():
                        self._log.debug("Stopping worker")
                        self.state = RunState.Stopping
                        self._event.reset()
                    elif self.wanted:
                        self._log.debug("Worker resuming")
                        self.state = RunState.Running

                case RunState.Stopping:
                    if self._event.wait():
                        self._attempt_stop()
                    else:
                        self._event.reset(delay=1)

                case RunState.Stopped:
                    self._event.wait()
                    if self.wanted:
                        self._log.debug("Starting worker")
                        self.state = RunState.Starting
                    else:
                        self._event.reset(delay=10)

                case _:
                    raise ValueError("Unknown state value")

        self._log.debug("Thread exit")

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
            if not (self.running and self.wanted):
                raise ServiceStoppedError(f"{self.name}: Service stopped while waiting for it to start")

            if self.state == RunState.Running:
                self._log.debug("Ready")
                return True

            self._log.debug(f"Awaiting ready ({self.state})")
            self.idle(timeout=0.4)

    def await_stopped(self):
        while True:
            if self.wanted:
                self._log.warning("Service started while waiting for it to stop")
                return False

            if self.state == RunState.Stopped:
                self._log.debug("Stopped")
                return True

            self._log.debug(f"Awaiting stopped ({self.state})")
            self.idle(timeout=0.4)


class ServiceManager:

    def __init__(self):
        self._log = logging.getLogger("ServiceManager")
        self.svcs = {}
        self.refs = {}
        atexit.register(self.atexit)

    def __iter__(self):
        return iter(self.svcs)

    def __contains__(self, name):
        return name in self.svcs

    def atexit(self):
        sys.stderr.write("\n")
        self._log.debug("Shutting down threads..")
        self.dump()
        trace.trace_all_threads()

        for svc in self.svcs.values():
            svc._shutdown = True

        for svc in self.svcs.values():
            if svc.state != RunState.Stopped:
                svc.stop()

        self.dump()

        self._log.debug("Waiting for threads to stop..")
        for svc in self.svcs.values():
            self._log.debug(f"Waiting for {svc.name}..")
            trace.trace_thread(svc)
            svc.await_stopped()

        self._log.debug("Cleaning up threads..")
        self.dump()
        for svc in self.svcs.values():
            svc.shutdown()

        self._log.info("Shutdown complete")

    def dump(self):
        self._log.debug("Service state")
        for name in self.svcs:
            svc = self.svcs[name]
            ref = self.refs[name]
            self._log.debug(f"  [{ref:>4}] {name:20} running={svc.running} state={svc.state} wanted={svc.wanted}")

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

    def stream(self, name: str):
        try:
            with self.borrow(name) as svc:
                queue = Queue()

                with svc.tap(lambda data: queue.put(data)):
                    while svc.state == RunState.Running:
                        yield queue.get()
        except (EOFError, OSError, ServiceStoppedError):
            return
