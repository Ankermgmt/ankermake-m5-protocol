import re
import sys
import os
import time
import click
import json
import logging as log
from flask import make_response, abort

from cli.model import DEFAULT_UPLOAD_RATE_MBPS, UPLOAD_RATE_MBPS_CHOICES

def require_python_version(major, minor):
    vi = sys.version_info
    if vi.major < major or vi.minor < minor:
        sys.stderr.write(
            "ERROR: Python version too old (%d.%d required but %d.%d installed)\n" % (
                major, minor,
                vi.major, vi.minor
            )
        )
        exit(1)


def json_key_value(str):
    if "=" not in str:
        raise ValueError("Invalid 'key=value' argument")
    key, value = str.split("=", 1)
    try:
        return key, int(value)
    except ValueError:
        try:
            return key, float(value)
        except ValueError:
            return key, value


class EnumType(click.ParamType):
    def __init__(self, enum):
        self.__enum = enum

    def get_missing_message(self, param):
        return "Choose number or name from:\n{choices}".format(
            choices="\n".join(f"{e.value:10}: {e.name}" for e in sorted(self.__enum))
        )

    def convert(self, value, param, ctx):
        try:
            return self.__enum(int(value))
        except ValueError:
            try:
                return self.__enum[value]
            except KeyError:
                self.fail(self.get_missing_message(param), param, ctx)


class FileSizeType(click.ParamType):

    name = "filesize"

    def convert(self, value, param, ctx):
        value = value.lower().rstrip("b")
        try:
            num = int(value[:-1])
            if value.endswith("k"):
                return num * 1024**1
            elif value.endswith("m"):
                return num * 1024**2
            elif value.endswith("g"):
                return num * 1024**3
            elif value.endswith("t"):
                return num * 1024**4
            else:
                raise ValueError()
        except ValueError:
            self.fail("Invalid file size: use {kb,gb,mb,tb} suffix (examples: 1337kb, 42mb, 17gb)", param, ctx)


def parse_json(msg):
    if isinstance(msg, dict):
        for key, value in msg.items():
            msg[key] = parse_json(value)
    elif isinstance(msg, str):
        try:
            msg = parse_json(json.loads(msg))
        except ValueError:
            pass

    return msg


def pretty_json(msg):
    return json.dumps(parse_json(msg), indent=4)


def pretty_mac(mac):
    parts = []
    while mac:
        parts.append(mac[:2])
        mac = mac[2:]
    return ":".join(parts)


def pretty_size(size):
    for unit in ["", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:3.2f}{unit}"


def split_chunks(data, chunksize):
    data = data[:]
    res = []
    while data:
        res.append(data[:chunksize])
        data = data[chunksize:]
    return res


def parse_http_bool(str):
    if str in {"true", "True", "1"}:
        return True
    elif str in {"false", "False", "0"}:
        return False
    else:
        raise ValueError(f"Could not parse {str!r} as boolean")


def http_abort(code, message):
    response = make_response(f"{message}")
    response.status_code = code
    abort(response)


class RateLimiter:
    def __init__(self, rate_mbps):
        self.rate_mbps = rate_mbps
        self.bytes_per_sec = rate_mbps * 125000
        self.start_time = time.monotonic()
        self.sent_bytes = 0

    def throttle(self, chunk_size):
        self.sent_bytes += chunk_size
        elapsed = time.monotonic() - self.start_time
        expected = self.sent_bytes / self.bytes_per_sec
        if expected > elapsed:
            time.sleep(expected - elapsed)


def _parse_upload_rate_mbps(value):
    if value is None:
        return None
    try:
        rate = int(value)
    except (TypeError, ValueError):
        return None
    if rate in UPLOAD_RATE_MBPS_CHOICES:
        return rate
    return None


def resolve_upload_rate_mbps(config=None, override=None, env_var="UPLOAD_RATE_MBPS"):
    if override is not None:
        rate = _parse_upload_rate_mbps(override)
        if rate is None:
            raise ValueError(f"Unsupported upload rate: {override}")
        return rate

    env_value = os.getenv(env_var)
    env_rate = _parse_upload_rate_mbps(env_value)
    if env_value is not None and env_rate is None:
        log.warning(f"Ignoring unsupported {env_var}={env_value!r}")
    if env_rate is not None:
        return env_rate
    if config is not None and hasattr(config, "upload_rate_mbps"):
        return config.upload_rate_mbps
    return DEFAULT_UPLOAD_RATE_MBPS


_TIME_PATTERN = re.compile(r";\s*estimated printing time[^=]*=\s*(.*)", re.IGNORECASE)
_TIME_UNITS   = {"d": 86400, "h": 3600, "m": 60, "s": 1}


def _parse_time_seconds(time_str):
    total = 0
    for value, unit in re.findall(r"(\d+)\s*([dhms])", time_str, re.IGNORECASE):
        total += int(value) * _TIME_UNITS[unit.lower()]
    return total or None


def patch_gcode_time(data: bytes) -> bytes:
    """Insert ;TIME:<seconds> before the first G28 if not already present.

    Parses the estimated print time from OrcaSlicer / PrusaSlicer comments
    ('; estimated printing time = 4h 44m 44s') and injects the AnkerMake
    compatible ;TIME: marker so the printer can display the remaining time.
    Returns the (possibly patched) bytes unchanged if the marker already
    exists or no parseable time comment is found.
    """
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        return data

    lines = text.splitlines(keepends=True)
    g28_index = None
    seconds = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.upper().startswith(";TIME:"):
            return data  # Already present — nothing to do

        if g28_index is None and stripped.upper().startswith("G28"):
            g28_index = i

        m = _TIME_PATTERN.search(line)
        if m and seconds is None:
            seconds = _parse_time_seconds(m.group(1))

        if g28_index is not None and seconds is not None:
            break

    if g28_index is None or seconds is None:
        return data

    lines.insert(g28_index, f";TIME:{seconds}\n")
    log.debug(f"patch_gcode_time: inserted ;TIME:{seconds} before line {g28_index + 1}")
    return "".join(lines).encode("utf-8")


_LAYER_COUNT_PATTERNS = [
    re.compile(r"^;LAYER_COUNT:(\d+)", re.IGNORECASE),
    re.compile(r"^;\s*total layer(?:s)?\s*(?:number|count)?\s*[=:]\s*(\d+)", re.IGNORECASE),
]


def extract_layer_count(data: bytes) -> int | None:
    """Extract the total layer count from GCode header comments.

    Supports OrcaSlicer (;LAYER_COUNT:N, ; total layer number: N)
    and PrusaSlicer (; total layers count = N) formats.
    Returns None if no layer count comment is found.
    """
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        return None

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith(";"):
            break  # Header ends at first non-comment line
        for pattern in _LAYER_COUNT_PATTERNS:
            m = pattern.match(line)
            if m:
                return int(m.group(1))
    return None
