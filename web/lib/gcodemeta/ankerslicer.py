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

    def _parse_head(self, data):
        res = {}

        for line in data.splitlines():
            line = line.decode()

            if not line.startswith(";"):
                continue

            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key[1:].lower().replace(" ", "_")
            res[f"_{key}"] = self.parse_prop(value.strip())

        return res

    def _parse_tail(self, data):
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

    def load_props(self, fd):
        headsize = 32 * 1024
        tailsize = 32 * 1024

        fd.seek(0, 2)
        fsize = fd.tell()

        if fsize > (headsize + tailsize):
            fd.seek(-tailsize, 2)
            tail = fd.read(tailsize)
            fd.seek(0)
            head = fd.read(headsize)
            return {
                **self._parse_head(head),
                **self._parse_tail(tail),
            }
        else:
            fd.seek(0)
            data = fd.read()
            return {
                **self._parse_head(data),
                **self._parse_tail(data),
            }

        return res
