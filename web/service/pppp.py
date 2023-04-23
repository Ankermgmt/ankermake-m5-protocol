import json

import logging as log

from ..lib.service import Service
from .. import app

from libflagship.pppp import P2PCmdType

import cli.pppp


class PPPPService(Service):

    def api_command(self, commandType, **kwargs):
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

    def worker_run(self, timeout):
        self.idle(timeout)

    def worker_stop(self):
        self.api.stop()
        del self.api
