from datetime import datetime
from platformdirs import PlatformDirs

from cli.config import BaseConfigManager
from ..lib.service import Service
from web.model import Job, JobQueue


class JobQueueService(Service):

    def worker_init(self):
        self.cfg = BaseConfigManager(PlatformDirs("ankerctl"), classes=(Job, JobQueue))
        try:
            self.queue = self.cfg.load("jobs", JobQueue(jobs=[]))
        except OSError:
            pass

    def worker_start(self):
        self.upd = self.app.svc.get("updates", ready=False)

    def worker_run(self, timeout):
        self.idle(timeout=timeout)

    def worker_stop(self):
        self.cfg.save("jobs", self.queue)

        self.app.svc.put("updates")

    def queued_jobs(self):
        return [j.to_dict() for j in self.queue.jobs]

    def queue_state(self):
        return {
            "queue_state": "ready",
            "queued_jobs": self.queued_jobs(),
        }

    def post_job(self, filename):
        self.queue.jobs.append(Job(
            filename=filename,
            job_id=bytes(filename, "utf-8"),
            # job_id=bytes(filename, "utf-8").hex().zfill(16),
            time_added=datetime.now(),
        ))

        self.upd.notify_job_queue_changed("jobs_added", self.queued_jobs(), "ready")

    def delete_jobs(self, job_ids):
        self.queue.jobs = [j for j in self.queue.jobs if not j.job_id in job_ids]

        self.upd.notify_job_queue_changed("jobs_removed", self.queued_jobs(), "ready")
