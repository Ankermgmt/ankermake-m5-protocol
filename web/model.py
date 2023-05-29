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
