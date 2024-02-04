import json
from datetime import datetime
from dataclasses import dataclass, MISSING
from libflagship.util import unhex, enhex


class Serialize:

    @classmethod
    def from_dict(cls, data):
        res = {}
        for k, v in cls.__dataclass_fields__.items():
            if (k not in data) and (v.default is not MISSING):
                # prevent KeyErrors if there is a default value
                res[k] = v.default
            else:
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
    country: str=""

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

    def __bool__(self):
        return bool(self.account)
