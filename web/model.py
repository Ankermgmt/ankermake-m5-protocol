import copy
import json
from datetime import datetime
from dataclasses import dataclass, asdict, field
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
class FileThumbnail(Serialize):
    width: int
    height: int
    size: int
    relative_path: str


@dataclass
class FileMetadata(Serialize):
    print_start_time:      str                 | None = None
    size:                  int                 | None = None
    modified:              float               | None = None
    uuid:                  str                 | None = None
    slicer:                str                 | None = None
    slicer_version:        str                 | None = None
    layer_height:          float               | None = None
    first_layer_height:    float               | None = None
    object_height:         float               | None = None
    thumbnails:            list[FileThumbnail] | None = field(default_factory=list)
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


@dataclass
class Job(Serialize):
    filename:      str
    job_id:        str
    time_added:    datetime
    exists:        bool            = True
    start_time:    datetime | None = None
    end_time:      datetime | None = None
    filament_used: float    | None = None
    metadata:      FileMetadata    = field(default_factory=FileMetadata)

    # cancelled, error, in_progress, klippy_shutdown, completed
    status:        str             = ""

    @property
    def time_in_queue(self):
        return datetime.now() - self.time_added

    @property
    def time_taken(self):
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()

    def to_dict(self, recursive=True):
        return {
            **super().to_dict(recursive),
            "time_in_queue": self.time_in_queue.total_seconds()
        }


@dataclass
class JobQueue(Serialize):
    jobs: list[Job]
