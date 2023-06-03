from dataclasses import dataclass, field

from cli.model import Serialize

#
# moonraker api printer objects
#

@dataclass(eq=False)
class Webhooks(Serialize):
    state:         str = ""
    state_message: str = ""


@dataclass(eq=False)
class PrintStatsInfo(Serialize):
    total_layer:   int = 0
    current_layer: int = 0


@dataclass(eq=False)
class PrintStats(Serialize):
    filename:       str   = ""
    total_duration: float = 0
    print_duration: float = 0
    filament_used:  float = 0
    state:          str   = ""
    message:        str   = ""
    info:           PrintStatsInfo = field(default_factory=PrintStatsInfo)


@dataclass(eq=False)
class Status(Serialize):
    webhooks: Webhooks = None


@dataclass(eq=False)
class HeaterBed(Serialize):
    temperature: float = 0
    target:      float = 0
    power:       float = 0


@dataclass(eq=False)
class Extruder(Serialize):
    temperature:      float = 0
    target:           float = 0
    power:            float = 0
    can_extrude:      bool = True
    pressure_advance: float = 0
    smooth_time:      float = 0


@dataclass(eq=False)
class Heaters(Serialize):
    available_heaters: list[str] = field(default_factory=lambda: ["heater_bed", "extruder"])
    available_sensors: list[str] = field(default_factory=lambda: ["heater_bed", "extruder"])


@dataclass(eq=False)
class DisplayStatus(Serialize):
    progress: float = 0
    message: str = ""


@dataclass(eq=False)
class IdleTimeout(Serialize):
    state: str = "Idle"
    printing_time: float = 0


@dataclass(eq=False)
class Toolhead(Serialize):
    homed_axes: str = ""
    axis_minimum: list[float] = field(default_factory=lambda: [0, 0, 0, 0])
    axis_maximum: list[float] = field(default_factory=lambda: [235, 235, 250, 0])
    print_time: float = None
    stalls: int = 0
    estimated_print_time: float = None
    extruder: str = "extruder"
    position: list[float] = field(default_factory=lambda: [0, 0, 0, 0])
    max_velocity: float = 600
    max_accel: float = 6000
    max_accel_to_decel: float = None
    square_corner_velocity: float = 10.6 # 15 / sqrt(2)


@dataclass(eq=False)
class Configfile(Serialize):
    config:                    dict      = field(default_factory=dict)
    settings:                  dict      = field(default_factory=dict)
    warnings:                  list[str] = field(default_factory=list)
    save_config_pending:       bool      = False
    save_config_pending_items: dict      = field(default_factory=dict)


@dataclass(eq=False)
class Mcu(Serialize):
    mcu_version:        str  = "Linux 4.4.94"
    mcu_build_versions: str  = "Ingenic r4.1.1-gcc720-glibc226-fp64 2020.11-05"
    mcu_constants:      dict = field(default_factory=dict)
    last_stats:         dict = field(default_factory=dict)


@dataclass(eq=False)
class GcodeMacro(Serialize):
    pass


@dataclass(eq=False)
class Steppers(Serialize):
    stepper_x: bool = False
    stepper_y: bool = False
    stepper_z: bool = False
    extruder:  bool = False


@dataclass(eq=False)
class StepperEnable(Serialize):
    stepper_enable: Steppers = field(default_factory=Steppers)


@dataclass(eq=False)
class GcodeMove(Serialize):
    speed_factor:         float       = 1
    speed:                float       = 1500
    extrude_factor:       float       = 1
    absolute_coordinates: bool        = True
    absolute_extrude:     bool        = True
    homing_origin:        list[float] = field(default_factory=lambda: [0, 0, 0, 0])
    position:             list[float] = field(default_factory=lambda: [0, 0, 0, 0])
    gcode_position:       list[float] = field(default_factory=lambda: [0, 0, 0, 0])


@dataclass(eq=False)
class ExcludeObject(Serialize):
    objects: list[str] = field(default_factory=list)
    excluded_objects: list[str] = field(default_factory=list)
    current_object: str | None = None


@dataclass(eq=False)
class BedMeshParams(Serialize):
    min_x:      float = 10
    max_x:      float = 225
    min_y:      float = 10
    max_y:      float = 225
    x_count:    int = 5
    y_count:    int = 5
    mesh_x_pps: int = 5
    mesh_y_pps: int = 5
    algo:       str = "bicubic"
    tension:    float = 0.2


@dataclass(eq=False)
class BedMeshProfile(Serialize):
    points: list[list[float]] = field(default_factory=lambda: [[]])
    mesh_params: list[BedMeshParams] = field(default_factory=list)


@dataclass(eq=False)
class BedMesh(Serialize):
    profile_name: str = ""
    mesh_min: list[float] = field(default_factory=lambda: [0, 0])
    mesh_max: list[float] = field(default_factory=lambda: [0, 0])
    probed_matrix: list[list[float]] = field(default_factory=lambda: [[]])
    mesh_matrix: list[list[float]] = field(default_factory=lambda: [[]])
    profiles: dict[str, BedMeshProfile] = field(default_factory=dict)


@dataclass(eq=False)
class SystemStats(Serialize):
    pass
