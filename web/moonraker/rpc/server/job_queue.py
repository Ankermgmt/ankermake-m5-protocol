from jsonrpc import dispatcher
from flask import current_app as app


@dispatcher.add_method(name="server.job_queue.status")
def server_job_queue_status():
    return {
        "queued_jobs": [],
        "queue_state": "ready",
    }


@dispatcher.add_method(name="server.job_queue.post_job")
def server_job_queue_post_job(filenames, reset=False):
    d = {
        "queued_jobs": [
            {
             "filename": filenames[0],
             "job_id": "0000000066D99C90",
             "time_added": 1636151050.7666452,
             "time_in_queue": 21.89680004119873
            }
        ],
        "queue_state": "ready",
    }
    with app.svc.borrow("updates") as upd:
        upd.notify_job_queue_changed("jobs_added", d["queued_jobs"], d["queue_state"])
    return d


@dispatcher.add_method(name="server.job_queue.delete_job")
def server_job_queue_delete_job(job_ids):
    ...


@dispatcher.add_method(name="server.job_queue.pause")
def server_job_queue_pause():
    ...


@dispatcher.add_method(name="server.job_queue.start")
def server_job_queue_start():
    ...


@dispatcher.add_method(name="server.job_queue.jump")
def server_job_queue_jump(job_id):
    ...
