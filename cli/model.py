import dataclasses
import json
from dataclasses import dataclass
from libflagship.util import unhex, enhex

class Serialize:

    @classmethod
    def from_dict(cls, data):
        res = {}
        for k, v in cls.__dataclass_fields__.items():
            res[k] = data[k]
            if v.type == bytes:
                res[k] = unhex(res[k])
        return cls(**res)

    def to_dict(self):
        res = {}
        for k, v in self.__dataclass_fields__.items():
            res[k] = getattr(self, k)
            if v.type == bytes:
                res[k] = enhex(res[k])
        return res

    @classmethod
    def from_json(cls, data):
        return cls.from_dict(json.loads(data))

    def to_json(self):
        return json.dumps(self.to_dict())

@dataclass
class Printer(Serialize):
    sn: str
    mqtt_key: bytes
    p2p_conn: str
    p2p_duid: str
    p2p_key: str

@dataclass
class Account(Serialize):
    auth_token: str
    mqtt_username: str
    mqtt_password: str
