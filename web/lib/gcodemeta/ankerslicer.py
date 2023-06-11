import re
import json

from base64 import b64decode

from web.model import FileMetadata, FileThumbnail
from web.lib.gcodemeta import GCodeMeta


re_slicer = re.compile("^;AnkerMake version: (\S+)")
re_thumb_begin = re.compile("; thumbnail begin (\d+) (\d+)")
re_thumb_end = re.compile("; thumbnail end")


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

    def _parse_slicer(self, data):
        res = {}
        for line in data.decode().splitlines():
            if m := re_slicer.match(line):
                res["__slicer_name"] = "AnkerSlicer"
                res["__slicer_version"] = m.group(1).removeprefix("V").replace("_", "-")

        return res

    def _parse_head(self, data):
        res = {}

        thumbs = []
        thumb = []
        thumb_size = None

        for line in data.splitlines():
            line = line.decode()

            if not line.startswith(";"):
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key[1:].lower().replace(" ", "_")
                res[f"_{key}"] = self.parse_prop(value.strip())
            elif m := re_thumb_begin.match(line):
                thumb = []
                thumb_size = [int(m.group(1)), int(m.group(2))]
            elif m := re_thumb_end.match(line):
                thumbs.append((thumb_size, b64decode("".join(thumb))))
                thumb = []
            else:
                thumb.append(line)

        if not thumbs:
            return res

        res["__thumbs"] = []
        for t in thumbs:
            res["__thumbs"].append({
                "width": t[0][0],
                "height": t[0][1],
                "data": t[1],
            })

        return res

    def _parse_tail(self, data):
        if not b";paramBegin" in data:
            return {}

        data = data.split(b";paramBegin", 1)[1]

        if not b";paramEnd" in data:
            return {}

        data, tail = data.split(b";paramEnd", 1)

        data = data.replace(b"\r\n;", b"")

        data = b64decode(data).decode()

        res = self._parse_slicer(tail)
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

    def load_metadata(self, props):
        return FileMetadata(
            print_start_time=None,
            size=None,
            modified=None,
            uuid=None,
            estimated_time=None,
            filename=None,
            first_layer_bed_temp=props.get("material_bed_temperature_layer_0"),
            first_layer_extr_temp=props.get("material_print_temperature_layer_0"),
            first_layer_height=props.get("layer_height_0"),
            gcode_end_byte=None,
            gcode_start_byte=None,
            layer_height=props.get("layer_height"),
            nozzle_diameter=props.get("machine_nozzle_size"),
            object_height=props.get("_maxz"),
            slicer=props.get("__slicer_name"),
            slicer_version=props.get("__slicer_version"),
            thumbnails=[],
            filament_name=props.get("filament_settings_id"),
            filament_type=props.get("filament_type") or props.get("meta_current_material_name"),
            filament_total=float(props.get("_filament_used", "0m")[:-1]) * 1000.0,
            filament_weight_total=float(props.get("_filament_weight", "0g")[:-1]),
        )
