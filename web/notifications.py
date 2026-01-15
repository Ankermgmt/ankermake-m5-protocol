import logging as log
import time

from libflagship.notifications import AppriseClient

from cli.model import (
    default_notifications_config,
    default_apprise_config,
    merge_dict_defaults,
)


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

    def include_image(self):
        progress = self.settings().get("progress", {})
        if isinstance(progress, dict):
            return bool(progress.get("include_image"))
        return False

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
