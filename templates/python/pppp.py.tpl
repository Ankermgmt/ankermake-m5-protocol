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
from .megajank import crypto_curse_string, crypto_decurse_string, simple_encrypt_string, simple_decrypt_string

%for enum in _pppp:
%if enum.expr == "enum":
class ${enum.name}(enum.IntEnum):
%for const in enum.consts:
    ${const.aligned_name} = ${const.aligned_hex_value} # ${"".join(const.comment or "unknown")}
%endfor

    @classmethod
    def parse(cls, p):
        return cls(struct.unpack("B", p[:1])[0]), p[1:]
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

## output all "struct" blocks
%for struct in _pppp.without("Message"):
%if struct.expr == "struct":
@dataclass
class ${struct.name}:
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
