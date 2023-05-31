import copy
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from cli.model import Serialize


@dataclass
class Heater:
    current: float = 0.0
    target: float = 0.0

    @classmethod
    def from_mqtt(cls, data):
        return cls(
            current=float(data["currentTemp"]) / 100,
            target=float(data["targetTemp"]) / 100
        )


@dataclass
class PrinterState:
    nozzle: Heater
    hotbed: Heater


@dataclass
class PrinterStats:
    nozzle: list[Heater]
    hotbed: list[Heater]

    def append(self, state: PrinterState):
        self.nozzle.append(copy.copy(state.nozzle))
        self.hotbed.append(copy.copy(state.hotbed))
        self.nozzle = self.nozzle[:1200]
        self.hotbed = self.hotbed[:1200]

    def save(self, fd):
        json.dump(asdict(self), fd)

    def load(self, fd):
        js = json.load(fd)
        self.nozzle = [Heater(**h) for h in js.get("nozzle", [])]
        self.hotbed = [Heater(**h) for h in js.get("hotbed", [])]


@dataclass
class Job(Serialize):
    filename: str
    job_id: bytes
    time_added: datetime

    @property
    def time_in_queue(self):
        return datetime.now() - self.time_added

    def to_dict(self):
        return {
            "time_in_queue": self.time_in_queue.total_seconds(),
            "filename": self.filename,
            "job_id": self.job_id.hex().zfill(16),
            "time_added": self.time_added.timestamp()
        }


@dataclass
class JobQueue(Serialize):
    jobs: list[Job]


@dataclass
class FileThumbnail(Serialize):
    width: int
    height: int
    size: int
    relative_path: str


@dataclass
class FileMetadata(Serialize):
    print_start_time:      str                 | None = None
    job_id:                str                 | None = None
    size:                  int                 | None = None
    modified:              float               | None = None
    uuid:                  str                 | None = None
    slicer:                str                 | None = None
    slicer_version:        str                 | None = None
    layer_height:          float               | None = None
    first_layer_height:    float               | None = None
    object_height:         float               | None = None
    filament_total:        float               | None = None
    estimated_time:        float               | None = None
    thumbnails:            list[FileThumbnail] | None = None
    first_layer_bed_temp:  float               | None = None
    first_layer_extr_temp: float               | None = None
    gcode_start_byte:      int                 | None = None
    gcode_end_byte:        int                 | None = None
    filename:              str                 | None = None
    estimated_time:        float               | None = None
    nozzle_diameter:       float               | None = None
    filament_name:         str                 | None = None
    filament_type:         str                 | None = None
    filament_total:        float               | None = None
    filament_weight_total: float               | None = None
