import json
import logging as log

from ..lib.service import Service
from .. import app

from libflagship.pppp import P2PSubCmdType
from libflagship.util import enhex


class VideoQueue(Service):

    def api_start_live(self):
        self.pppp.api_command(P2PSubCmdType.START_LIVE, data={
            "encryptkey": "x",
            "accountId": "y",
        })

    def api_stop_live(self):
        self.pppp.api_command(P2PSubCmdType.CLOSE_LIVE)

    def api_light_state(self, light):
        self.pppp.api_command(P2PSubCmdType.LIGHT_STATE_SWITCH, data={
            "open": light,
        })

    def api_video_mode(self, mode):
        self.pppp.api_command(P2PSubCmdType.LIVE_MODE_SET, data={
            "mode": mode
        })

    def worker_start(self):
        self.pppp = app.svc.get("pppp")
        self.api_start_live()

    def worker_run(self, timeout):
        d = self.pppp.api.recv_xzyh(chan=1, timeout=timeout)
        if not d:
            return

        log.debug(f"Video data packet: {enhex(d.data):32}...")
        self.notify(d.data)

    def worker_stop(self):
        self.api_stop_live()
        app.svc.put("pppp")
