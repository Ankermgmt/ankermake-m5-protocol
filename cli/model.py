import json
from datetime import datetime
from dataclasses import dataclass, field
from libflagship.util import unhex, enhex


DEFAULT_UPLOAD_RATE_MBPS = 10
UPLOAD_RATE_MBPS_CHOICES = (5, 10, 25, 50, 100)


def default_apprise_config():
    return {
        "enabled": False,
        "server_url": "",
        "key": "",
        "tag": "",
        "events": {
            "print_started": True,
            "print_finished": True,
            "print_failed": True,
            "gcode_uploaded": True,
            "print_progress": True,
        },
        "progress": {
            "interval_percent": 25,
            "include_image": False,
            "snapshot_quality": "hd",
            "snapshot_fallback": True,
        },
        "templates": {
            "print_started": "Print started: {filename}",
            "print_finished": "Print finished: {filename} ({duration})",
            "print_failed": "Print failed: {filename} ({reason})",
            "gcode_uploaded": "Upload complete: {filename} ({size})",
            "print_progress": "Progress: {percent}% - {filename}",
        },
    }


def default_notifications_config():
    return {
        "apprise": default_apprise_config(),
    }


def merge_dict_defaults(data, defaults):
    if not isinstance(data, dict):
        return defaults

    merged = {}
    for key, default_value in defaults.items():
        if isinstance(default_value, dict):
            merged[key] = merge_dict_defaults(data.get(key), default_value)
        else:
            merged[key] = data.get(key, default_value)

    for key, value in data.items():
        if key not in merged:
            merged[key] = value

    return merged


class Serialize:

    @classmethod
    def from_dict(cls, data):
        res = {}
        for k, v in cls.__dataclass_fields__.items():
            res[k] = data[k]
            if v.type == bytes:
                res[k] = unhex(res[k])
            elif v.type == datetime:
                res[k] = datetime.fromtimestamp(res[k])
        return cls(**res)

    def to_dict(self):
        res = {}
        for k, v in self.__dataclass_fields__.items():
            res[k] = getattr(self, k)
            if v.type == bytes:
                res[k] = enhex(res[k])
            elif v.type == datetime:
                res[k] = res[k].timestamp()
        return res

    @classmethod
    def from_json(cls, data):
        return cls.from_dict(json.loads(data))

    def to_json(self):
        return json.dumps(self.to_dict())


@dataclass
class Printer(Serialize):
    id: str
    sn: str
    name: str
    model: str
    create_time: datetime
    update_time: datetime
    wifi_mac: str
    ip_addr: str
    mqtt_key: bytes
    api_hosts: str
    p2p_hosts: str
    p2p_duid: str
    p2p_key: str


@dataclass
class Account(Serialize):
    auth_token: str
    region: str
    user_id: str
    email: str

    @property
    def mqtt_username(self):
        return f"eufy_{self.user_id}"

    @property
    def mqtt_password(self):
        return self.email


@dataclass
class Config(Serialize):
    account: Account
    printers: list[Printer]
    upload_rate_mbps: int = DEFAULT_UPLOAD_RATE_MBPS
    notifications: dict = field(default_factory=default_notifications_config)

    @classmethod
    def from_dict(cls, data):
        if "upload_rate_mbps" not in data:
            data = {**data, "upload_rate_mbps": DEFAULT_UPLOAD_RATE_MBPS}
        data = {
            **data,
            "notifications": merge_dict_defaults(
                data.get("notifications"),
                default_notifications_config(),
            ),
        }
        return super().from_dict(data)

    def __bool__(self):
        return bool(self.account)
