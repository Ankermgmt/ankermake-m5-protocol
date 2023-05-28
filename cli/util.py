import sys
import click
import json
from flask import make_response, abort


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

def make_mqtt_req(command_type, args):
    cmd = { "commandType": command_type }
    for path, value in args:
        path = path.split(".")
        obj = cmd
        for step in path[:-1]:
            obj = obj.setdefault(step, {})

        obj[path[-1]] = value

    return cmd


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
