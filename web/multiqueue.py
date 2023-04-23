import contextlib

from multiprocessing import Queue

from .lib.service import Service


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
