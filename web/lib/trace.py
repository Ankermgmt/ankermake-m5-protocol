import sys
import traceback
import threading
import logging


log = logging.getLogger("trace")


def log_stack(stack):
    stk = traceback.format_list(traceback.extract_stack(stack))
    log.debug("-"*120)
    for line in "".join(stk).splitlines():
        if line.startswith("  File"):
            line = line[2:]
        log.debug(line)
    log.debug("-"*120)


def trace_all_threads():
    frames = sys._current_frames()

    for thread in threading.enumerate():
        log.debug(f"Thread {thread}")
        log_stack(frames[thread.ident])


def trace_thread(thread):
    frames = sys._current_frames()
    log_stack(frames[thread.ident])
