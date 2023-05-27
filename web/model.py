from dataclasses import dataclass


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
