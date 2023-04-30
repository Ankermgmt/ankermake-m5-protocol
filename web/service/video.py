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
        self.saved_light_state = light
        self.pppp.api_command(P2PSubCmdType.LIGHT_STATE_SWITCH, data={
            "open": light,
        })

    def api_video_mode(self, mode):
        self.saved_video_mode = mode
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

    def worker_init(self):
        self.saved_light_state = None
        self.saved_video_mode = None

    def worker_start(self):
        self.pppp = app.svc.get("pppp")

        self.api_id = id(self.pppp._api)

        self.pppp.handlers.append(self._handler)

        self.api_start_live()

        if self.saved_light_state is not None:
            self.api_light_state(self.saved_light_state)

        if self.saved_video_mode is not None:
            self.api_video_mode(self.saved_video_mode)

    def worker_run(self, timeout):
        self.idle(timeout=timeout)

        if not self.pppp.connected:
            raise ServiceRestartSignal("No pppp connection")

        if id(self.pppp._api) != self.api_id:
            raise ServiceRestartSignal("New pppp connection detected, restarting video feed")

    def worker_stop(self):
        try:
            self.api_stop_live()
        except ConnectionError:
            pass

        self.pppp.handlers.remove(self._handler)

        app.svc.put("pppp")
