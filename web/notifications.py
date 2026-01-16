import logging as log
import os
import shutil
import subprocess
import tempfile
import threading
import time

from libflagship.notifications import AppriseClient

from web import app
from web.lib.service import RunState, ServiceStoppedError

from cli.model import (
    default_notifications_config,
    default_apprise_config,
    merge_dict_defaults,
)

_SNAPSHOT_SIZES = {
    "hd": (1280, 720),
    "fhd": (1920, 1080),
}
_DEFAULT_SNAPSHOT_QUALITY = "hd"
_SNAPSHOT_TIMEOUT = 6


def format_duration(seconds):
    if seconds is None:
        return ""
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return ""
    if seconds < 0:
        seconds = 0
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_bytes(num_bytes):
    if num_bytes is None:
        return ""
    try:
        size = float(num_bytes)
    except (TypeError, ValueError):
        return ""
    if size <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 0
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1
    precision = 0 if size >= 10 or idx == 0 else 1
    return f"{size:.{precision}f} {units[idx]}"


class AppriseNotifier:
    def __init__(self, config_manager, reload_interval=5.0):
        self._config_manager = config_manager
        self._reload_interval = reload_interval
        self._last_load = 0.0
        self._client = None
        self._settings = None
        self._snapshot_lock = threading.Lock()

    def _load(self):
        now = time.monotonic()
        if self._client and (now - self._last_load) < self._reload_interval:
            return

        try:
            with self._config_manager.open() as cfg:
                if not cfg:
                    self._client = None
                    self._settings = None
                    self._last_load = now
                    return
                notifications = merge_dict_defaults(
                    getattr(cfg, "notifications", None),
                    default_notifications_config(),
                )
                apprise_config = merge_dict_defaults(
                    notifications.get("apprise"),
                    default_apprise_config(),
                )
        except Exception as err:
            log.warning(f"Failed to load apprise config: {err}")
            self._client = None
            self._settings = None
            self._last_load = now
            return

        self._client = AppriseClient(apprise_config)
        self._settings = self._client.settings
        self._last_load = now

    def client(self):
        self._load()
        return self._client

    def settings(self):
        self._load()
        return self._settings or {}

    def progress_interval(self, default=25):
        progress = self.settings().get("progress", {})
        interval = None
        if isinstance(progress, dict):
            interval = progress.get("interval_percent")
        try:
            interval = int(interval)
        except (TypeError, ValueError):
            interval = default
        if interval < 1:
            interval = 1
        if interval > 100:
            interval = 100
        return interval

    def progress_max(self):
        progress = self.settings().get("progress", {})
        max_value = None
        if isinstance(progress, dict):
            max_value = progress.get("max_value")
        try:
            max_value = int(max_value)
        except (TypeError, ValueError):
            return None
        if max_value <= 0:
            return None
        return max_value

    def include_image(self):
        progress = self.settings().get("progress", {})
        if isinstance(progress, dict):
            return bool(progress.get("include_image"))
        return False

    def snapshot_quality(self, default=_DEFAULT_SNAPSHOT_QUALITY):
        progress = self.settings().get("progress", {})
        quality = None
        if isinstance(progress, dict):
            quality = progress.get("snapshot_quality")
        if not isinstance(quality, str):
            return default
        quality = quality.strip().lower()
        if quality not in _SNAPSHOT_SIZES:
            return default
        return quality

    def build_attachments(self, preview_url=None):
        if not self.include_image():
            return None, []
        snapshot = self._capture_live_snapshot()
        if snapshot:
            return [snapshot], [snapshot]
        if preview_url:
            return [preview_url], []
        return None, []

    def cleanup_attachments(self, paths):
        for path in paths:
            try:
                os.remove(path)
            except OSError:
                pass

    def send(self, event, payload=None, attachments=None):
        client = self.client()
        if not client or not client.is_enabled():
            return False, "Apprise disabled"
        if not client.is_event_enabled(event):
            return False, "Event disabled"

        ok, message = client.send(event, payload=payload, attachments=attachments)
        if not ok:
            log.warning(f"Apprise notify failed: {message}")
        return ok, message

    def _capture_live_snapshot(self):
        if not app.config.get("video_supported"):
            return None
        if not shutil.which("ffmpeg"):
            log.warning("Apprise snapshot skipped: ffmpeg not available")
            return None

        vq = app.svc.svcs.get("videoqueue")
        if not vq:
            return None

        host = os.getenv("FLASK_HOST") or "127.0.0.1"
        if host in {"0.0.0.0", "::"}:
            host = "127.0.0.1"
        port = os.getenv("FLASK_PORT") or "4470"
        url = f"http://{host}:{port}/video"

        quality = self.snapshot_quality()
        width, height = _SNAPSHOT_SIZES.get(quality, _SNAPSHOT_SIZES[_DEFAULT_SNAPSHOT_QUALITY])
        scale_filter = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        )

        was_enabled = vq.video_enabled
        temp_path = None

        with self._snapshot_lock:
            try:
                if not was_enabled:
                    vq.set_video_enabled(True)
                if vq.state == RunState.Stopped:
                    vq.start()
                if vq.state != RunState.Running:
                    vq.await_ready()

                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp_path = temp_file.name
                temp_file.close()

                def run_ffmpeg(extra_args=None):
                    cmd = [
                        "ffmpeg",
                        "-loglevel",
                        "error",
                        "-nostdin",
                        "-y",
                    ]
                    if extra_args:
                        cmd.extend(extra_args)
                    cmd.extend([
                        "-i",
                        url,
                        "-frames:v",
                        "1",
                        "-vf",
                        scale_filter,
                        temp_path,
                    ])
                    return subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=_SNAPSHOT_TIMEOUT,
                    )

                result = run_ffmpeg(["-f", "h264"])
                if result.returncode != 0:
                    result = run_ffmpeg()

                if result.returncode != 0 or not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                    if result.returncode != 0:
                        stderr = result.stderr.decode(errors="ignore").strip()
                        if stderr:
                            log.warning(f"Apprise snapshot failed: {stderr}")
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                    return None
                return temp_path
            except (OSError, subprocess.SubprocessError, ServiceStoppedError, subprocess.TimeoutExpired) as err:
                log.warning(f"Apprise snapshot failed: {err}")
                if temp_path:
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                return None
            finally:
                if not was_enabled:
                    vq.set_video_enabled(False)
