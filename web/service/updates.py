from datetime import datetime

from ..lib.service import Service, Holdoff
from .. import rpcutil
from web.model import PrinterState, PrinterStats, Heater
from web.moonraker.model import BedMeshParams
from web.moonraker.lib.updatemgr import UpdateManager

from libflagship.mqtt import MqttMsgType


def parse_leveling_grid(data):
    lines = data.splitlines()

    if not lines[0].startswith("Bilinear Leveling Grid:"):
        return

    if not lines[1].split()[0] == "0":
        return

    if not lines[2].split()[0] == "0":
        return

    res = []
    for line in lines[2:9]:
        res.append([float(n) for n in line.split()[1:]])

    return res


class UpdateNotifierService(Service):

    def mqtt_to_jsonrpc_req(self, data):
        pstate = self.pstate
        umgr = self.umgr
        match data.get("commandType", 0):
            case MqttMsgType.ZZ_MQTT_CMD_HOTBED_TEMP:
                pstate.hotbed = Heater.from_mqtt(data)
                umgr.heater_bed.temperature = pstate.hotbed.current
                umgr.heater_bed.target = pstate.hotbed.target
                umgr.heater_bed.power = int(pstate.hotbed.target > pstate.hotbed.current)

            case MqttMsgType.ZZ_MQTT_CMD_NOZZLE_TEMP:
                pstate.nozzle = Heater.from_mqtt(data)
                umgr.extruder.temperature = pstate.nozzle.current
                umgr.extruder.target = pstate.nozzle.target
                umgr.extruder.power = int(pstate.nozzle.target > pstate.nozzle.current)

            case MqttMsgType.ZZ_MQTT_CMD_AUTO_LEVELING:
                index = data.get("value", 0)
                if index < 50:
                    umgr.display_status.message = "Bed leveling in progress.."
                    umgr.display_status.progress = float(index) / 49.0

                    umgr.virtual_sdcard.progress = float(index) / 49.0
                    umgr.virtual_sdcard.file_position = None

                    umgr.print_stats.total_duration = 1
                    umgr.print_stats.print_duration = 1
                    umgr.print_stats.filament_used = 1
                    umgr.print_stats.filename = None
                    umgr.print_stats.state = "printing"
                else:
                    umgr.display_status.message = None
                    umgr.display_status.progress = None

            case MqttMsgType.ZZ_MQTT_CMD_PRINT_SCHEDULE:
                total = 670
                time = data.get("time", 0)
                umgr.print_stats.total_duration = total - time
                umgr.print_stats.print_duration = total - time

            case MqttMsgType.ZZ_MQTT_CMD_MOTOR_LOCK:
                locked = data.get("value", 0)
                umgr.toolhead.homed_axes = "xyz" if locked else ""

            case MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND:
                result = data["resData"]
                result = result.rstrip().removesuffix("+ringbuf:1,512,0").rstrip()

                if result.startswith("Bilinear Leveling Grid"):
                    umgr.bed_mesh.profile_name = "anker-builtin"
                    umgr.bed_mesh.probed_matrix = parse_leveling_grid(result)
                    umgr.bed_mesh.profiles = {
                        "anker-builtin": {
                            "points": umgr.bed_mesh.probed_matrix,
                            "mesh_params": BedMeshParams(),
                        }
                    }
                else:
                    return rpcutil.make_jsonrpc_req("notify_gcode_response", result)

            case _:
                return None

    def notify_error(self, message):
        self.notify(rpcutil.make_jsonrpc_req("notify_gcode_response", f"!! {message}"))

    def notify_status_update(self, **kwargs):
        self.notify(rpcutil.make_jsonrpc_req("notify_status_update", kwargs, datetime.now().timestamp()))

    def notify_job_queue_changed(self, action, queue, state):
        self.notify(rpcutil.make_jsonrpc_req("notify_job_queue_changed", {
            "action": action,
            "updated_queue": queue,
            "queue_state": state,
        }))

    def _handler(self, data):
        upd = self.mqtt_to_jsonrpc_req(data)
        if upd:
            self.notify(upd)

    def worker_init(self):
        self.pstate = PrinterState(nozzle=Heater(), hotbed=Heater())
        self.pstats = PrinterStats(nozzle=[], hotbed=[])
        self.holdoff = Holdoff()
        self.holdoff.reset(delay=1)
        self.umgr = UpdateManager()
        try:
            with open("stats.json") as fd:
                self.pstats.load(fd)
        except OSError:
            pass

    def worker_start(self):
        self.mqtt = self.app.svc.get("mqttqueue", ready=False)

        self.mqtt.handlers.append(self._handler)

    def worker_run(self, timeout):
        if self.holdoff.passed:
            self.holdoff.reset(delay=1)
            self.pstats.append(self.pstate)
            self.notify(rpcutil.make_jsonrpc_req("notify_status_update", {}))

        if update := self.umgr.moonraker_status_update():
            self.notify(rpcutil.make_jsonrpc_req("notify_status_update", update))

        self.idle(timeout=timeout)

    def worker_stop(self):
        with open("stats.json", "w") as fd:
            self.pstats.save(fd)
        self.mqtt.handlers.remove(self._handler)

        self.app.svc.put("mqttqueue")
