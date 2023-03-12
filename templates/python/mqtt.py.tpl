<% import python %>\
${python.header()}

import enum
from dataclasses import dataclass
from .amtypes import *

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
