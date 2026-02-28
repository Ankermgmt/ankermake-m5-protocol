<% import python %>\
${python.header()}

import enum
from dataclasses import dataclass
import json
from .amtypes import *
from .megajank import mqtt_checksum_add, mqtt_checksum_remove, mqtt_aes_encrypt, mqtt_aes_decrypt

% for enum in _mqtt:
% if enum.expr == "enum":
class ${enum.name}(enum.IntEnum):
    % for const in enum.consts:
    ${const.aligned_name} = ${const.aligned_hex_value} # ${const.comment[0]}
    % endfor

    @classmethod
    def parse(cls, p):
        return cls(struct.unpack("B", p[:1])[0]), p[1:]

    def pack(self):
        return struct.pack("B", self)

% endif
% endfor
% for struct in _mqtt:
% if struct.expr == "struct":
@dataclass
class ${struct.name}:
    % for field in struct.fields:
    ${field.aligned_name}: ${python.typename(field)} # ${"".join(field.comment)}
    % endfor

    @classmethod
    def parse(cls, p):
    %for field in struct.fields:
        ${field.name}, p = ${python.typeparse(field, "p")}
    %endfor
        return cls(${", ".join(f"{f.name}={f.name}" for f in struct.fields)}), p

    def pack(self):
        p  = ${python.typepack(struct.fields[0])}
    %for field in struct.fields[1:]:
        p += ${python.typepack(field)}
    %endfor
        return p

% endif
% endfor

class MqttMsg(_MqttMsg):

    # Header body length by m5 format byte:
    #   m5=1  AnkerMake M5C — 24-byte header (no time / device_guid fields, 12-byte padding)
    #   m5=2  AnkerMake M5  — 64-byte header (full fields)
    _HEADER_LEN = {1: 24, 2: 64}

    @classmethod
    def _parse_m5c(cls, p):
        """Parse an M5C-format (m5=1) message with a 24-byte header.

        The M5C omits the time and device_guid fields present in the M5 format
        and uses a 12-byte padding block instead of 11 bytes.
        """
        signature, p = Magic.parse(p, 2, b'MA')
        size, p = u16le.parse(p)
        m3, p = u8.parse(p)
        m4, p = u8.parse(p)
        m5, p = u8.parse(p)
        m6, p = u8.parse(p)
        m7, p = u8.parse(p)
        packet_type, p = MqttPktType.parse(p)
        packet_num, p = u16le.parse(p)
        padding, p = Bytes.parse(p, 12)
        data, p = Tail.parse(p)
        return cls(
            signature=signature, size=size, m3=m3, m4=m4, m5=m5,
            m6=m6, m7=m7, packet_type=packet_type, packet_num=packet_num,
            time=0, device_guid="", padding=padding, data=data,
        ), p

    @classmethod
    def parse(cls, p, key):
        p = mqtt_checksum_remove(p)
        if len(p) < 7:
            raise ValueError(f"MQTT message too short ({len(p)} bytes)")
        m5 = p[6]
        try:
            body_len = cls._HEADER_LEN[m5]
        except KeyError:
            raise ValueError(f"Unsupported mqtt message format (expected 1 or 2, but found {m5})")
        body, encrypted = p[:body_len], p[body_len:]
        data = mqtt_aes_decrypt(encrypted, key)
        if m5 == 1:
            return cls._parse_m5c(body + data)
        res = super().parse(body + data)
        if res[0].size != (len(p) + 1):
            raise ValueError(f"MQTT message size mismatch (header={res[0].size}, actual={len(p) + 1})")
        return res

    def pack(self, key):
        try:
            body_len = self._HEADER_LEN[self.m5]
        except KeyError:
            raise ValueError(f"Cannot pack unsupported mqtt message format (m5={self.m5})")
        data = mqtt_aes_encrypt(self.data, key)
        self.size = body_len + len(data) + 1
        if self.m5 == 1:
            # M5C: first 12 common bytes, then exactly 12 bytes of padding (no time/guid)
            m5c_padding = (self.padding + b'\x00' * 12)[:12]
            body = super().pack()[:12] + m5c_padding
        else:
            body = super().pack()[:64]
        final = mqtt_checksum_add(body + data)
        return final

    def getjson(self):
        return json.loads(self.data.decode())

    def setjson(self, val):
        self.data = json.dumps(val).encode()
