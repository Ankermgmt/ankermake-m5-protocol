import logging as log
from multiprocessing import Queue

from ..lib.service import Service

from libflagship.util import enhex
from libflagship.mqtt import MqttMsgType

import cli.mqtt


class MqttQueue(Service):

    def api_command(self, cmd, userid="ankerctl", **kwargs):
        self.queue.put({
            "commandType": int(cmd),
            "userid": userid,
            **kwargs,
        })

    def api_gcode(self, gcode):
        # printer firmware cannot reliably handle the same gcode twice in a
        # row, so put a blank space at the end, if we get a repeat command.
        gcode = gcode.strip()
        if gcode == self._last_gcode:
            gcode += " "
        self.api_command(
            MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND,
            cmdData=gcode,
            cmdLen=len(gcode),
        )
        self._last_gcode = gcode

    def worker_init(self):
        self._last_gcode = ""
        self.queue = Queue()

    def worker_start(self):
        config = self.app.config
        self.client = cli.mqtt.mqtt_open(
            config["config"],
            config["printer_index"],
            config["insecure"]
        )

    def worker_run(self, timeout):
        while not self.queue.empty():
            msg = self.queue.get()
            log.info(f"COMMAND [{msg}]")
            self.client.command(msg)

        for msg, body in self.client.fetch(timeout=timeout):
            log.info(f"TOPIC [{msg.topic}]")
            log.debug(enhex(msg.payload[:]))

            for obj in body:
                self.notify(obj)

    def worker_stop(self):
        del self.client
