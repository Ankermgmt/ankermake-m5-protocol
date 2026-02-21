import logging
import time
import uuid

from ..lib.service import Service
from .. import app

from libflagship.pppp import FileTransfer
from libflagship.ppppapi import FileUploadInfo, PPPPError

import cli.util
import cli.pppp
from cli.util import patch_gcode_time

log = logging.getLogger(__name__)

from libflagship.notifications.events import EVENT_GCODE_UPLOADED
from ..notifications import AppriseNotifier, format_bytes


class FileTransferService(Service):

    REPLY_TIMEOUT = 10.0
    PROGRESS_INTERVAL = 0.25

    def worker_init(self):
        self._notifier = AppriseNotifier(app.config["config"])

    def worker_run(self, timeout):
        self.idle(timeout=timeout)

    def _notify_upload(self, payload):
        try:
            self.notify(payload)
        except Exception as e:
            log.warning(f"Upload progress notify failed: {e}")

    def send_file(self, fd, user_name, rate_limit_mbps=None, start_print=True):
        data = patch_gcode_time(fd.read())
        user_id = "-"
        try:
            with app.config["config"].open() as cfg:
                if cfg and cfg.account and cfg.account.user_id:
                    user_id = cfg.account.user_id
        except Exception:
            pass
        file_uuid = uuid.uuid4().hex.upper()
        fui = FileUploadInfo.from_data(data, fd.filename, user_name=user_name, user_id=user_id, machine_id=file_uuid)
        log.info(f"Going to upload {fui.size} bytes as {fui.name!r}")
        upload_name = fui.name
        self._notify_upload({"status": "start", "name": upload_name, "size": fui.size})
        if rate_limit_mbps:
            log.info(f"Using upload rate limit: {rate_limit_mbps} Mbps")
        pppp_dump = app.config.get("pppp_dump")
        last_emit = 0.0

        def progress_cb(sent, total):
            nonlocal last_emit
            now = time.monotonic()
            if sent < total and now - last_emit < self.PROGRESS_INTERVAL:
                return
            last_emit = now
            self._notify_upload({
                "status": "progress",
                "name": upload_name,
                "size": total,
                "sent": sent,
            })
        try:
            api = cli.pppp.pppp_open(
                app.config["config"],
                app.config["printer_index"],
                timeout=self.REPLY_TIMEOUT,
                dumpfile=pppp_dump,
            )
        except Exception as e:
            self._notify_upload({"status": "error", "name": upload_name, "error": str(e)})
            raise ConnectionError(f"No pppp connection to printer: {e}") from e
        try:
            cli.pppp.pppp_send_file(
                api,
                fui,
                data,
                rate_limit_mbps=rate_limit_mbps,
                progress_cb=progress_cb,
                show_progress=False,
            )
            if start_print:
                log.info("File upload complete. Requesting print start of job.")
                api.aabb_request(b"", frametype=FileTransfer.END)
            else:
                log.info("File upload complete (upload-only)")
        except ConnectionError as e:
            log.error(f"Could not send print job: {e}")
            self._notify_upload({"status": "error", "name": upload_name, "error": str(e)})
            raise
        except (PPPPError, OSError, EOFError) as e:
            log.error(f"Could not send print job: {e}")
            self._notify_upload({"status": "error", "name": upload_name, "error": str(e)})
            raise ConnectionError(f"PPPP transfer failed: {e}") from e
        except Exception as e:
            log.error(f"Could not send print job: {e}")
            self._notify_upload({"status": "error", "name": upload_name, "error": str(e)})
            raise
        else:
            if start_print:
                log.info("Successfully sent print job")
            else:
                log.info("Successfully uploaded file")
            self._notify_upload({
                "status": "done",
                "name": upload_name,
                "size": fui.size,
                "sent": fui.size,
            })
            self._notify_apprise_upload(upload_name, fui.size, start_print)
        finally:
            api.stop()

    def _notify_apprise_upload(self, filename, size_bytes, start_print):
        payload = {
            "filename": filename,
            "size": format_bytes(size_bytes),
            "size_bytes": size_bytes,
            "start_print": bool(start_print),
        }
        self._notifier.send(EVENT_GCODE_UPLOADED, payload=payload)
