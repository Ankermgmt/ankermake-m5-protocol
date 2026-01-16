import logging as log
import os
import tempfile
from urllib.parse import urlparse

import requests

from .events import EVENT_ENV_OVERRIDES, EVENT_TITLES

DEFAULT_TIMEOUT = 10

_BOOL_TRUE = {"1", "true", "yes", "on", "y", "t"}
_BOOL_FALSE = {"0", "false", "no", "off", "n", "f"}


class SafeDict(dict):

    def __missing__(self, key):
        return "{" + key + "}"


def _parse_bool(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _BOOL_TRUE:
        return True
    if text in _BOOL_FALSE:
        return False
    return None


def _parse_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _read_bool_env(env, env_var):
    env_value = env.get(env_var)
    parsed = _parse_bool(env_value)
    if env_value is not None and parsed is None:
        log.warning(f"Ignoring unsupported {env_var}={env_value!r}")
    return parsed


def _read_int_env(env, env_var):
    env_value = env.get(env_var)
    parsed = _parse_int(env_value)
    if env_value is not None and parsed is None:
        log.warning(f"Ignoring unsupported {env_var}={env_value!r}")
    return parsed


def _normalize_server_url(server_url):
    if not server_url:
        return server_url
    if isinstance(server_url, str):
        return server_url.strip().rstrip("/")
    return server_url


def _normalize_attachments(attachments):
    if not attachments:
        return None
    if isinstance(attachments, (list, tuple, set)):
        normalized = [item for item in attachments if item]
    else:
        normalized = [attachments]
    return normalized or None


def _is_url(value):
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _attachment_name_from_url(url):
    try:
        parsed = urlparse(url)
    except Exception:
        return "attachment"
    name = os.path.basename(parsed.path)
    return name or "attachment"


class AppriseClient:

    def __init__(self, config=None, env=None, timeout=DEFAULT_TIMEOUT):
        self._raw_config = config if config is not None else {}
        self._env = env if env is not None else os.environ
        self._timeout = timeout
        self._settings = self._resolve_settings(self._raw_config, self._env)

    def _resolve_settings(self, config, env):
        settings = dict(config) if isinstance(config, dict) else {}
        settings["events"] = dict(settings.get("events") or {})
        settings["progress"] = dict(settings.get("progress") or {})
        settings["templates"] = dict(settings.get("templates") or {})

        enabled = _read_bool_env(env, "APPRISE_ENABLED")
        if enabled is not None:
            settings["enabled"] = enabled

        server_url = env.get("APPRISE_SERVER_URL")
        if server_url is not None:
            settings["server_url"] = server_url

        key = env.get("APPRISE_KEY")
        if key is not None:
            settings["key"] = key

        tag = env.get("APPRISE_TAG")
        if tag is not None:
            settings["tag"] = tag

        for event, env_var in EVENT_ENV_OVERRIDES.items():
            override = _read_bool_env(env, env_var)
            if override is not None:
                settings["events"][event] = override

        interval = _read_int_env(env, "APPRISE_PROGRESS_INTERVAL")
        if interval is not None:
            settings["progress"]["interval_percent"] = interval

        include_image = _read_bool_env(env, "APPRISE_PROGRESS_INCLUDE_IMAGE")
        if include_image is not None:
            settings["progress"]["include_image"] = include_image

        snapshot_quality = env.get("APPRISE_SNAPSHOT_QUALITY")
        if snapshot_quality is not None:
            settings["progress"]["snapshot_quality"] = snapshot_quality

        progress_max = _read_int_env(env, "APPRISE_PROGRESS_MAX")
        if progress_max is not None:
            settings["progress"]["max_value"] = progress_max

        return settings

    @property
    def settings(self):
        return self._settings

    def is_configured(self):
        return bool(self._server_url()) and bool(self._key())

    def is_enabled(self):
        return bool(self._settings.get("enabled")) and self.is_configured()

    def is_event_enabled(self, event):
        return bool(self._settings.get("events", {}).get(event, False))

    def render_template(self, event, payload=None):
        template = self._settings.get("templates", {}).get(event)
        if not template:
            return self._fallback_template(event, payload)
        data = payload if isinstance(payload, dict) else {}
        return template.format_map(SafeDict(data))

    def send(self, event, payload=None, title=None, body=None, attachments=None):
        if not self.is_enabled():
            return False, "Apprise is disabled or missing required settings"
        if not self.is_event_enabled(event):
            return False, f"Event disabled: {event}"

        if body is None:
            body = self.render_template(event, payload)
        if title is None:
            title = EVENT_TITLES.get(event, "Ankerctl")
        return self._post(title, body, attachments=attachments)

    def test_connection(self):
        if not self.is_configured():
            return False, "Apprise server URL or key missing"
        return self._post("Ankerctl test", "Apprise test notification")

    def _fallback_template(self, event, payload):
        if payload is None:
            return event
        return f"{event}: {payload}"

    def _server_url(self):
        return _normalize_server_url(self._settings.get("server_url"))

    def _key(self):
        key = self._settings.get("key")
        if isinstance(key, str):
            return key.strip().strip("/")
        return key

    def _notify_url(self):
        server_url = self._server_url()
        key = self._key()
        if not server_url or not key:
            return None
        if server_url.endswith("/notify"):
            base = server_url
        else:
            base = f"{server_url}/notify"
        return f"{base}/{key}"

    def _post(self, title, body, attachments=None):
        url = self._notify_url()
        if not url:
            return False, "Apprise server URL or key missing"

        tag = self._settings.get("tag")
        if isinstance(tag, str):
            tag = tag.strip()
        if tag:
            tag_value = tag
        else:
            tag_value = None

        attach = _normalize_attachments(attachments)
        if attach:
            attach_result = self._post_with_attachments(url, title, body, tag_value, attach)
            if attach_result is not None:
                return attach_result

        payload = {"title": title, "body": body}
        if tag_value:
            payload["tag"] = tag_value
        if attach:
            payload["attach"] = attach
        try:
            response = requests.post(url, json=payload, timeout=self._timeout)
        except requests.RequestException as err:
            log.warning(f"Apprise request failed: {err}")
            return False, str(err)

        return self._parse_response(response)

    def _post_with_attachments(self, url, title, body, tag, attachments):
        files = {}
        file_handles = []
        temp_paths = []
        attach_index = 1

        try:
            for item in attachments:
                if not isinstance(item, str):
                    continue
                if _is_url(item):
                    try:
                        response = requests.get(item, stream=True, timeout=self._timeout)
                        response.raise_for_status()
                    except requests.RequestException as err:
                        log.warning(f"Apprise attachment download failed: {item} ({err})")
                        continue

                    suffix = os.path.splitext(urlparse(item).path)[1]
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                    try:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                temp_file.write(chunk)
                    finally:
                        temp_file.close()
                        response.close()

                    temp_paths.append(temp_file.name)
                    filename = _attachment_name_from_url(item)
                    fp = open(temp_file.name, "rb")
                    file_handles.append(fp)
                    files[f"attach{attach_index}"] = (filename, fp)
                    attach_index += 1
                else:
                    path = os.path.expanduser(item)
                    if not os.path.isfile(path):
                        log.warning(f"Apprise attachment not found: {item}")
                        continue
                    fp = open(path, "rb")
                    file_handles.append(fp)
                    files[f"attach{attach_index}"] = (os.path.basename(path), fp)
                    attach_index += 1

            if not files:
                return None

            data = {"title": title, "body": body}
            if tag:
                data["tag"] = tag

            response = requests.post(url, data=data, files=files, timeout=self._timeout)
            return self._parse_response(response)
        except requests.RequestException as err:
            log.warning(f"Apprise request failed: {err}")
            return False, str(err)
        finally:
            for fp in file_handles:
                try:
                    fp.close()
                except Exception:
                    pass
            for path in temp_paths:
                try:
                    os.remove(path)
                except OSError:
                    pass

    def _parse_response(self, response):
        data = None
        try:
            data = response.json()
        except ValueError:
            data = None

        if not response.ok:
            message = None
            if isinstance(data, dict):
                message = data.get("error") or data.get("message")
            if not message:
                message = f"{response.status_code} {response.reason}"
            return False, message

        if isinstance(data, dict) and data.get("success") is False:
            return False, data.get("error") or data.get("message") or "Apprise error"

        if isinstance(data, dict) and data.get("message"):
            return True, data["message"]
        return True, "Notification sent"
