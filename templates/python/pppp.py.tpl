<% import python %>\
${python.header()}

<%def name="encrypt(struct)">\
    %if struct.const("@crypto_type", 0) == 1:
        p = simple_encrypt_string(p)\
    %elif struct.const("@crypto_type", 0) == 2:
        p = crypto_curse_string(p)\
    %else:
        # not encrypted\
    %endif
</%def>\
##
##
<%def name="decrypt(struct)">\
    %if struct.const("@crypto_type", 0) == 1:
        p = simple_decrypt_string(p)\
    %elif struct.const("@crypto_type", 0) == 2:
        p = crypto_decurse_string(p)\
    %else:
        # not encrypted\
%endif
</%def>\
##
##
<%def name="pack_fields(struct)">\
%if len(struct.fields) > 0:
        p  = ${python.typepack(struct.fields[0])}
    %for field in struct.fields[1:]:
        p += ${python.typepack(field)}
    %endfor
%else:
        p = b""
%endif
</%def>\
##
##
<%def name="unpack_fields(struct)">\
    %for field in struct.fields:
        ${field.name}, p = ${python.typeparse(field, "p")}
    %endfor
</%def>\
##
##
<%def name="declare_fields(struct)">\
    %for field in struct.fields:
    ${field.aligned_name} : ${python.typename(field)} # ${"".join(field.comment or "unknown")}
    %endfor
</%def>\
##
##
import struct
import enum
from dataclasses import dataclass, field
from .amtypes import *
from .amtypes import _assert_equal
from .megajank import crypto_curse_string, crypto_decurse_string, simple_encrypt_string, simple_decrypt_string
from .util import ppcs_crc16

%for enum in _pppp:
%if enum.expr == "enum":
class ${enum.name}(enum.IntEnum):
%for const in enum.consts:
    ${const.aligned_name} = ${const.aligned_hex_value} # ${"".join(const.comment or "unknown")}
%endfor

    @classmethod
    def parse(cls, p, typ=u8):
        d = typ.parse(p)
        return cls(d[0]), d[1]

    def pack(self, typ=u8):
        return typ.pack(self)

%endif
%endfor

@dataclass
class Message:

    type: Type = field(repr=False, init=False)

    @classmethod
    def parse(cls, m):
        magic, type, size = struct.unpack(">BBH", m[:4])
        assert magic == 0xF1
        type = Type(type)
        p = m[4:4+size]
        if type in MessageTypeTable:
            return MessageTypeTable[type].parse(p)
        else:
            raise ValueError(f"unknown message type {type:02x}")

    def pack(self, p):
        return struct.pack(">BBH", 0xF1, self.type, len(p)) + p

class _Host:
    pass

class _Duid:

    @classmethod
    def from_string(cls, str):
        prefix, serial, check = str.split("-")
        return cls(prefix, int(serial), check)

    def __str__(self):
        return f"{self.prefix}-{self.serial:06}-{self.check}"

class _Xzyh:
    pass

class _Aabb:

    @classmethod
    def parse_with_crc(cls, m):
        head, m = m[:12], m[12:]
        header = cls.parse(head)[0]
        data, m = m[:header.len], m[header.len:]
        crc1, m  = m[:2], m[2:]
        crc2 = ppcs_crc16(head[2:] + data)
        _assert_equal(crc1, crc2)
        return header, data, m

    def pack_with_crc(self, data):
        header = self.pack()

        return header + data + ppcs_crc16(header[2:] + data)

class _Dsk:
    pass

class _Version:
    pass

## output all "struct" blocks
%for struct in _pppp.without("Message"):
%if struct.expr == "struct":
@dataclass
class ${struct.name}(_${struct.name}):
${declare_fields(struct)}
    @classmethod
    def parse(cls, p):
${decrypt(struct)}
${unpack_fields(struct)}
        return cls(${", ".join(f"{f.name}={f.name}" for f in struct.fields)}), p

    def pack(self):
${pack_fields(struct)}
${encrypt(struct)}
        return p

%endif
%endfor

## output all "packet" blocks
%for struct in _pppp.without("Message"):
%if struct.expr == "packet":
@dataclass
class ${struct.name}(Message):
%for f in _pppp.get("MessageType").fields:
  %if f.type.name == struct.name:
    type = Type.${f.name}
  %endif
%endfor
${declare_fields(struct)}
    @classmethod
    def parse(cls, p):
${decrypt(struct)}
${unpack_fields(struct)}
        return cls(${", ".join(f"{f.name}={f.name}" for f in struct.fields)}), p

    def pack(self):
${pack_fields(struct)}
${encrypt(struct)}
        return super().pack(p)

%endif
%endfor

%for struct in _pppp:
%if struct.expr == "parser":
${struct.name}Table = {
    %for field in struct.fields:
    ${struct.field("@type").type}.${field.aligned_name} : ${field.type},
    %endfor
}

%endif
%endfor
