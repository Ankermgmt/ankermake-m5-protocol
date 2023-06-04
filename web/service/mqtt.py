import logging as log
from multiprocessing import Queue

from ..lib.service import Service

from libflagship.util import enhex
from libflagship.mqtt import MqttMsgType

import cli.mqtt


class MqttQueue(Service):

    def api_command(self, msg):
        self.queue.put(msg)

    def api_gcode(self, gcode):
        self.api_command({
            "commandType": MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND.value,
            "userid": "ankerctl",
            "cmdData": gcode,
            "cmdLen": len(gcode),
        })

    def worker_start(self):
        config = self.app.config
        self.client = cli.mqtt.mqtt_open(
            config["config"],
            config["printer_index"],
            config["insecure"]
        )
        self.queue = Queue()

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
