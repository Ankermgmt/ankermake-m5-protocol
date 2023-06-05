import uuid
from pathlib import Path
from datetime import datetime
from platformdirs import PlatformDirs

from cli.config import BaseConfigManager
from ..lib.service import Service
from web.model import Job, JobQueue, FileMetadata
from web.lib.gcodemeta import GCodeMetaAuto
from web.lib.gcodemeta.ankerslicer import GCodeMetaAnkerSlicer
from web.lib.gcodemeta.prusaslicer import GCodeMetaPrusaSlicer
from web.lib.gcodemeta.superslicer import GCodeMetaSuperSlicer


class JobQueueService(Service):

    def worker_init(self):
        self.cfg = BaseConfigManager(PlatformDirs("ankerctl"), classes=(Job, JobQueue, FileMetadata))
        try:
            self.queue = self.cfg.load("jobs", JobQueue(jobs=[], history=[]))
        except OSError:
            pass
        self.gcode_loader = GCodeMetaAuto([
            GCodeMetaAnkerSlicer(),
            GCodeMetaPrusaSlicer(),
            GCodeMetaSuperSlicer(),
        ])

    def worker_start(self):
        self.upd = self.app.svc.get("updates", ready=False)

    def worker_run(self, timeout):
        self.idle(timeout=timeout)

    def worker_stop(self):
        self.cfg.save("jobs", self.queue)

        self.app.svc.put("updates")

    def load_metadata(self, path: Path):
        stat = path.stat()
        fd = path.open("rb")

        gcm = self.gcode_loader
        if gcm.detect(fd):
            props = gcm.load_props(fd)
            md = gcm.load_metadata(props)
        else:
            md = FileMetadata()

        md.size = stat.st_size
        md.modified = stat.st_mtime
        md.filename = str(path)
        return md

    def load_metadata_dict(self, path: Path):
        md = self.load_metadata(path).to_dict()
        for h in self.queue.history:
            if h.filename == path:
                md["job_id"] = h.job_id
                md["uuid"] = h.metadata.uuid
                break

        return md

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
            job_id=self.queue.next_job_id(),
            time_added=datetime.now(),
        ))

        self.upd.notify_job_queue_changed("jobs_added", self.queued_jobs(), "ready")

    def delete_jobs(self, job_ids):
        self.queue.jobs = [j for j in self.queue.jobs if not j.job_id in job_ids]

        self.upd.notify_job_queue_changed("jobs_removed", self.queued_jobs(), "ready")
