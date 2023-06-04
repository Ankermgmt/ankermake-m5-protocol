from jsonrpc import dispatcher
from flask import current_app as app

from libflagship.util import unhex


@dispatcher.add_method(name="server.job_queue.status")
def server_job_queue_status():
    with app.svc.borrow("jobqueue") as jq:
        return jq.queue_state()


@dispatcher.add_method(name="server.job_queue.post_job")
def server_job_queue_post_job(filenames, reset=False):
    with app.svc.borrow("jobqueue") as jq:
        if reset:
            jq.queue.jobs.clear()

        for filename in filenames:
            jq.post_job(filename)

        return jq.queue_state()


@dispatcher.add_method(name="server.job_queue.delete_job")
def server_job_queue_delete_job(job_ids):
    with app.svc.borrow("jobqueue") as jq:
        jq.delete_jobs(job_ids)

        return jq.queue_state()


@dispatcher.add_method(name="server.job_queue.pause")
def server_job_queue_pause():
    ...


@dispatcher.add_method(name="server.job_queue.start")
def server_job_queue_start():
    ...


@dispatcher.add_method(name="server.job_queue.jump")
def server_job_queue_jump(job_id):
    ...
