import logging as log
import time

from ..lib.service import Service
from .. import app

from libflagship.util import enhex
from libflagship.mqtt import MqttMsgType
from libflagship.notifications.events import (
    EVENT_PRINT_STARTED,
    EVENT_PRINT_FINISHED,
    EVENT_PRINT_FAILED,
    EVENT_PRINT_PROGRESS,
)

import cli.mqtt
from ..notifications import AppriseNotifier, format_duration


class MqttQueue(Service):

    def worker_init(self):
        self._notifier = AppriseNotifier(app.config["config"])
        self._reset_print_state()

    def worker_start(self):
        self.client = cli.mqtt.mqtt_open(
            app.config["config"],
            app.config["printer_index"],
            app.config["insecure"]
        )
        self._reset_print_state()

    def _reset_print_state(self):
        self._print_active = False
        self._print_started_at = None
        self._last_progress = None
        self._last_progress_bucket = None
        self._last_filename = None
        self._last_task_id = None
        self._failure_sent = False
        self._preview_url = None

    def worker_run(self, timeout):
        for msg, body in self.client.fetch(timeout=timeout):
            log.info(f"TOPIC [{msg.topic}]")
            log.debug(enhex(msg.payload[:]))

            for obj in body:
                self.notify(obj)
                self._handle_notification(obj)

    def worker_stop(self):
        del self.client

    @staticmethod
    def _safe_int(value):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_progress(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        is_fractional = isinstance(value, float)
        if isinstance(value, str) and "." in value:
            is_fractional = True
        if number < 0:
            return 0
        if 0 < number <= 1 and is_fractional:
            number *= 100
        elif number > 100:
            if number <= 1000:
                number /= 10
            elif number <= 10000:
                number /= 100
            else:
                number = 100
        return int(number)

    @staticmethod
    def _extract_progress(payload):
        if not isinstance(payload, dict):
            return None
        if "progress" in payload:
            return MqttQueue._normalize_progress(payload.get("progress"))
        for key, value in payload.items():
            if isinstance(key, str) and "progress" in key.lower():
                progress = MqttQueue._normalize_progress(value)
                if progress is not None:
                    return progress
            if isinstance(value, dict) and "progress" in value:
                progress = MqttQueue._normalize_progress(value.get("progress"))
                if progress is not None:
                    return progress
        return None

    @staticmethod
    def _extract_filename(payload):
        for key in ("name", "fileName", "filename", "file_name", "gcode", "gcode_name"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _extract_time(payload, keys):
        for key in keys:
            if key in payload:
                value = MqttQueue._safe_int(payload.get(key))
                if value is not None:
                    return value
        return None

    @staticmethod
    def _extract_preview_url(payload):
        for key in (
            "preview_url",
            "previewUrl",
            "previewImageUrl",
            "preview_image_url",
            "image_url",
            "imageUrl",
            "img",
            "img_url",
            "imgUrl",
            "url",
        ):
            value = payload.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value

        for key, value in payload.items():
            if not isinstance(key, str) or not isinstance(value, str):
                continue
            if "preview" in key.lower() and value.startswith(("http://", "https://")):
                return value
        return None

    @staticmethod
    def _extract_failure_reason(payload):
        for key in ("error", "errorMsg", "errorMessage", "failReason", "reason"):
            value = payload.get(key)
            if value:
                return str(value)
        status = payload.get("status") or payload.get("state") or payload.get("printStatus")
        if isinstance(status, str):
            status_text = status.lower()
            if any(word in status_text for word in ("fail", "error", "abort", "cancel", "stop")):
                return status
        return None

    @staticmethod
    def _extract_task_id(payload):
        for key in ("task_id", "taskId", "taskID", "taskid"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _extract_status_text(payload):
        for key in ("status", "state", "printStatus", "statusType", "result"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower()
        return None

    def _handle_notification(self, payload):
        if not isinstance(payload, dict):
            return

        command_type = payload.get("commandType")
        preview_url = self._extract_preview_url(payload)
        if preview_url:
            self._preview_url = preview_url

        if command_type not in (
            MqttMsgType.ZZ_MQTT_CMD_PRINT_SCHEDULE,
            MqttMsgType.ZZ_MQTT_CMD_EVENT_NOTIFY,
        ):
            return

        progress = self._extract_progress(payload)
        if progress is None:
            return
        if progress < 0:
            progress = 0
        if progress > 100:
            progress = 100

        task_id = self._extract_task_id(payload)
        if task_id:
            if self._last_task_id and task_id != self._last_task_id and self._print_active:
                if progress <= 1:
                    self._reset_print_state()
                    self._last_task_id = task_id
                else:
                    task_id = self._last_task_id
            else:
                self._last_task_id = task_id

        filename = self._extract_filename(payload)
        if filename:
            if self._last_filename and filename != self._last_filename and self._print_active:
                if progress <= 1:
                    self._reset_print_state()
                    self._last_filename = filename
                else:
                    filename = self._last_filename
            else:
                self._last_filename = filename

        if self._last_progress is not None and progress < self._last_progress and progress <= 1:
            self._reset_print_state()

        failure_reason = self._extract_failure_reason(payload)
        if failure_reason and self._print_active and not self._failure_sent:
            self._send_event(
                EVENT_PRINT_FAILED,
                self._build_payload(payload, progress, failure_reason=failure_reason),
            )
            self._failure_sent = True
            self._print_active = False
            return

        if 0 < progress < 100 and not self._print_active:
            self._print_active = True
            self._print_started_at = time.monotonic()
            self._failure_sent = False
            self._last_progress_bucket = None
            self._send_event(
                EVENT_PRINT_STARTED,
                self._build_payload(payload, progress),
            )

        status_text = self._extract_status_text(payload)
        if self._print_active and status_text:
            if any(word in status_text for word in ("finish", "complete", "done")):
                self._send_event(
                    EVENT_PRINT_FINISHED,
                    self._build_payload(payload, 100),
                    include_image=True,
                )
                self._reset_print_state()
                return

        if self._print_active and progress >= 100:
            self._send_event(
                EVENT_PRINT_FINISHED,
                self._build_payload(payload, 100),
                include_image=True,
            )
            self._reset_print_state()
            return

        self._emit_progress(payload, progress)
        self._last_progress = progress

    def _emit_progress(self, payload, progress):
        if not self._print_active:
            return
        if progress <= 0 or progress >= 100:
            return
        interval = self._notifier.progress_interval()
        bucket = progress // interval
        if bucket <= 0:
            return
        if self._last_progress_bucket is not None and bucket <= self._last_progress_bucket:
            return
        self._last_progress_bucket = bucket
        self._send_event(
            EVENT_PRINT_PROGRESS,
            self._build_payload(payload, progress),
            include_image=True,
        )

    def _build_payload(self, payload, progress, failure_reason=None):
        elapsed = self._extract_time(payload, ("totalTime", "elapsed", "elapsedTime"))
        remaining = self._extract_time(payload, ("time", "remainTime", "remaining", "remainingTime"))
        duration = None
        if elapsed is not None and remaining is not None:
            duration = elapsed + remaining
        elif elapsed is not None:
            duration = elapsed
        elif self._print_started_at is not None:
            duration = int(time.monotonic() - self._print_started_at)

        filename = self._extract_filename(payload) or self._last_filename or "-"
        payload_out = {
            "filename": filename,
            "percent": progress,
            "elapsed_seconds": elapsed if elapsed is not None else "",
            "remaining_seconds": remaining if remaining is not None else "",
            "duration_seconds": duration if duration is not None else "",
            "elapsed": format_duration(elapsed),
            "remaining": format_duration(remaining),
            "duration": format_duration(duration),
        }
        if failure_reason:
            payload_out["reason"] = failure_reason
        return payload_out

    def _send_event(self, event, payload, include_image=False):
        attachments = None
        if include_image and self._notifier.include_image() and self._preview_url:
            attachments = [self._preview_url]
        self._notifier.send(event, payload=payload, attachments=attachments)
