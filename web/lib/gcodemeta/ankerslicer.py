import json
from web.lib.gcodemeta import GCodeMeta
from base64 import b64decode

class GCodeMetaAnkerSlicer(GCodeMeta):

    def detect_first_line(self, line):
        return b";Recompiled by AnkerMake" in line

    @staticmethod
    def parse_prop(val):
        if val.startswith('"[') and val.endswith(']"'):
            val = val[1:-1]

        try:
            return json.loads(val)
        except json.decoder.JSONDecodeError:
            return val

    def load_props(self, fd):
        rsize = 128 * 1024
        fd.seek(0, 2)
        fsize = fd.tell()
        size = min(fsize, rsize)
        fd.seek(-size, 2)
        data = fd.read(size)

        if not b";paramBegin" in data:
            return {}

        data = data.split(b";paramBegin", 1)[1]

        if not b";paramEnd" in data:
            return {}

        data = data.split(b";paramEnd", 1)[0]

        data = data.replace(b"\r\n;", b"")

        data = b64decode(data).decode()

        res = {}
        for line in data.splitlines():
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            res[key] = self.parse_prop(value)

        return res
