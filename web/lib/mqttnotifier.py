import time
import logging as log
from threading import Thread
from datetime import datetime

from libflagship.mqtt import MqttMsgType

from .. import rpcutil, app


def mqtt_to_jsonrpc_req(data):
    update = {
        "eventtime": datetime.now().timestamp(),
    }

    cmd = data.get("commandType", 0)
    if cmd == MqttMsgType.ZZ_MQTT_CMD_HOTBED_TEMP:
        app.hotbed_target_temp = float(data["targetTemp"]) / 100
        update["heater_bed"] = {
            "temperature": float(data["currentTemp"]) / 100,
            "target": app.hotbed_target_temp,
            "power": None,
        }
    elif cmd == MqttMsgType.ZZ_MQTT_CMD_NOZZLE_TEMP:
        app.heater_target_temp = float(data["targetTemp"]) / 100
        update["extruder"] = {
            "temperature": float(data["currentTemp"]) / 100,
            "target": app.heater_target_temp,
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


class MqttNotifier(Thread):

    def run(self):
        log.info("Waiting for mqttq service..")
        while not hasattr(app, "mqttq"):
            time.sleep(0.1)

        log.info("Found mqttq service")
        with app.mqttq.tap() as queue:
            while True:
                try:
                    data = queue.get()
                except EOFError:
                    break

                upd = mqtt_to_jsonrpc_req(data)
                if not upd:
                    continue

                for ws in app.websockets:
                    ws.send(upd)
