<% import python %>\
${python.header()}

import struct
import enum
from dataclasses import dataclass, field
import socket

def _assert_equal(value, expected):
    if value != expected:
        raise ValueError(f"expected {expected} but found {value}")

class Zeroes:
    @classmethod
    def parse(cls, p, num):
        body = p[:num]
        _assert_equal(set(body) - {0}, set())
        return body, p[num:]

    def pack(self, num):
        return b"\x00" * num

class Bytes(bytes):
    @classmethod
    def parse(cls, p, size):
        return p[:size], p[size:]

    def pack(self, size):
        return self

class String(Bytes):
    @classmethod
    def parse(cls, p, size):
        body, p = super().parse(p, size)
        _assert_equal(body[-1], 0)
        return body[:-1].decode(), p

    def pack(self, size):
        return self[:size-1].ljust(size, '\x00').encode()

class Array:
    @classmethod
    def parse(cls, p, elem, num):
        res = []
        for _ in range(num):
            item, p = elem.parse(p)
            res.append(item)
        return res, p

    def pack(self, cls, num):
        return b"".join(cls.pack(e) for e in self)

class IPv4(str):
    @classmethod
    def parse(cls, p):
        addr = p[:4][::-1]
        return cls(socket.inet_ntoa(addr)), p[4:]

    def pack(self):
        return socket.inet_aton(self)[::-1]

class Magic(bytes):
    @classmethod
    def parse(cls, p, size, expected):
        v, p = p[:size], p[size:]
        _assert_equal(v, expected)
        return cls(v), p

    def pack(self, size, expected):
        return self

class Tail(bytes):
    @classmethod
    def parse(cls, p):
        return cls(p), b""

    def pack(self):
        if isinstance(self, bytes):
            return self
        else:
            return self.pack()

class IntType(int):
    pass

%for name, desc, size in [ \
                            ("i8", "b", 1), \
                            ("u8", "B", 1), \
                            ("i16", "h", 2), \
                            ("u16", "H", 2), \
                            ("i32", "i", 4), \
                            ("u32", "I", 4), \
                           ]:
class ${name}be(IntType):
    size = ${size}

    @classmethod
    def parse(cls, p):
        return cls(struct.unpack(">${desc}", p[:cls.size])[0]), p[cls.size:]

    def pack(self):
        return struct.pack(">${desc}", self)

class ${name}le(IntType):
    size = ${size}

    @classmethod
    def parse(cls, p):
        return cls(struct.unpack("<${desc}", p[:cls.size])[0]), p[cls.size:]

    def pack(self):
        return struct.pack("<${desc}", self)

${name} = ${name}be

%endfor
