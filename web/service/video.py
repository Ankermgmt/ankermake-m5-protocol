import json
import logging as log

from queue import Empty
from multiprocessing import Queue

from ..lib.service import Service, ServiceRestartSignal
from .. import app

from libflagship.pppp import P2PSubCmdType, Xzyh


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

    def _handler(self, data):
        chan, msg = data

        if chan != 1:
            return

        if not isinstance(msg, Xzyh):
            return

        self.notify(msg)

    def worker_start(self):
        self.pppp = app.svc.get("pppp")

        self.api_id = id(self.pppp._api)

        self.pppp.handlers.append(self._handler)

        self.api_start_live()

    def worker_run(self, timeout):
        if not self.pppp.connected:
            raise ServiceRestartSignal("No pppp connection")

        if id(self.pppp._api) != self.api_id:
            raise ServiceRestartSignal("New pppp connection detected, restarting video feed")

    def worker_stop(self):
        self.api_stop_live()
        self.pppp.handlers.remove(self._handler)

        app.svc.put("pppp")
