import copy
from datetime import datetime

from ..lib.service import Service, Holdoff
from .. import rpcutil
from web.model import PrinterState, PrinterStats, Heater

from libflagship.mqtt import MqttMsgType


class UpdateNotifierService(Service):

    def mqtt_to_jsonrpc_req(self, data):
        update = {
            "eventtime": datetime.now().timestamp(),
        }

        cmd = data.get("commandType", 0)
        if cmd == MqttMsgType.ZZ_MQTT_CMD_HOTBED_TEMP:
            self.pstate.hotbed = Heater.from_mqtt(data)
            update["heater_bed"] = {
                "temperature": self.pstate.hotbed.current,
                "target": self.pstate.hotbed.target,
                "power": None,
            }
        elif cmd == MqttMsgType.ZZ_MQTT_CMD_NOZZLE_TEMP:
            self.pstate.nozzle = Heater.from_mqtt(data)
            update["extruder"] = {
                "temperature": self.pstate.nozzle.current,
                "target": self.pstate.nozzle.target,
                "power": 0,
                "can_extrude": True,
                "pressure_advance": None,
                "smooth_time": None,
                "motion_queue": None,
            }
        elif cmd == MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND:
            return rpcutil.make_jsonrpc_req("notify_gcode_response", data["resData"])
        else:
            return None

        return rpcutil.make_jsonrpc_req("notify_status_update", update)

    def notify_error(self, message):
        self.notify(rpcutil.make_jsonrpc_req("notify_gcode_response", f"!! {message}"))

    def _handler(self, data):
        upd = self.mqtt_to_jsonrpc_req(data)
        if upd:
            self.notify(upd)

    def worker_init(self):
        self.pstate = PrinterState(nozzle=Heater(), hotbed=Heater())
        self.pstats = PrinterStats(nozzle=[], hotbed=[])
        self.holdoff = Holdoff()
        self.holdoff.reset(delay=1)

    def worker_start(self):
        self.mqtt = self.app.svc.get("mqttqueue", ready=False)

        self.mqtt.handlers.append(self._handler)

    def worker_run(self, timeout):
        if self.holdoff.passed:
            self.holdoff.reset(delay=1)
            self.pstats.append(self.pstate)

        self.idle(timeout=timeout)

    def worker_stop(self):
        self.mqtt.handlers.remove(self._handler)

        self.app.svc.put("mqttqueue")
