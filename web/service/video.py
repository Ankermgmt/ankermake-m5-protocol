import json
import logging as log

from ..lib.service import Service
from .. import app

from libflagship.pppp import P2PSubCmdType, P2PCmdType
from libflagship.util import enhex

import cli.mqtt


class VideoQueue(Service):

    def send_command(self, commandType, **kwargs):
        cmd = {
            "commandType": commandType,
            **kwargs
        }
        return self.api.send_xzyh(
            json.dumps(cmd).encode(),
            cmd=P2PCmdType.P2P_JSON_CMD
        )

    def worker_start(self):
        self.api = cli.pppp.pppp_open(app.config["config"], timeout=1, dumpfile=app.config.get("pppp_dump"))

        self.send_command(P2PSubCmdType.START_LIVE, data={"encryptkey": "x", "accountId": "y"})

    def worker_run(self, timeout):
        d = self.api.recv_xzyh(chan=1, timeout=timeout)
        if not d:
            return

        log.debug(f"Video data packet: {enhex(d.data):32}...")
        self.notify(d.data)

    def worked_stop(self):
        self.api.send_command(P2PSubCmdType.CLOSE_LIVE)
