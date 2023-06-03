from ..model import *

class UpdateManager:

    def __init__(self):
        self.obj = {
            "webhooks":       Webhooks(),
            "print_stats":    PrintStats(),
            "heater_bed":     HeaterBed(),
            "extruder":       Extruder(),
            "heaters":        Heaters(),
            "display_status": DisplayStatus(),
            "idle_timeout":   IdleTimeout(),
            "toolhead":       Toolhead(),
            "configfile":     Configfile(),
            "mcu":            Mcu(),
            "stepper_enable": StepperEnable(),
            "gcode_move":     GcodeMove(),
            "exclude_object": ExcludeObject(),
            "bed_mesh":       BedMesh(),
            "system_stats":   SystemStats(),
        }
        self.snapshot()

    def snapshot(self):
        self.ref = { key: hash(value) for key, value in self.obj.items() }

    def compare(self):
        for key, value in self.obj.items():
            if hash(value) != self.ref.get(key):
                yield key

    def __contains__(self, k):
        return k in self.obj

    def __getitem__(self, k):
        return self.obj[k]

    @property
    def webhooks(self):
        return self.obj.get("webhooks")

    @property
    def print_stats(self):
        return self.obj.get("print_stats")

    @property
    def heater_bed(self):
        return self.obj.get("heater_bed")

    @property
    def extruder(self):
        return self.obj.get("extruder")

    @property
    def heaters(self):
        return self.obj.get("heaters")

    @property
    def display_status(self):
        return self.obj.get("display_status")

    @property
    def idle_timeout(self):
        return self.obj.get("idle_timeout")

    @property
    def toolhead(self):
        return self.obj.get("toolhead")

    @property
    def configfile(self):
        return self.obj.get("configfile")

    @property
    def mcu(self):
        return self.obj.get("mcu")

    @property
    def stepper_enable(self):
        return self.obj.get("stepper_enable")

    @property
    def gcode_move(self):
        return self.obj.get("gcode_move")

    @property
    def exclude_object(self):
        return self.obj.get("exclude_object")

    @property
    def bed_mesh(self):
        return self.obj.get("bed_mesh")

    @property
    def system_stats(self):
        return self.obj.get("system_stats")
