import json
import logging as log

from queue import Empty
from multiprocessing import Queue

from ..lib.service import Service
from .. import app

from libflagship.pppp import P2PSubCmdType, Xzyh
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
        self._tap = Queue()

        def handler(data):
            self._tap.put(data)

        self._handler = handler
        self.pppp.handlers.append(handler)

        self.api_start_live()

    def worker_run(self, timeout):
        try:
            data = self._tap.get(timeout=timeout)
        except (Empty, OSError):
            return

        if not data:
            return

        chan, msg = data

        if chan != 1:
            return

        if not isinstance(msg, Xzyh):
            return

        log.debug(f"Video data packet: {enhex(msg.data):32}...")
        self.notify(msg.data)

    def worker_stop(self):
        self.api_stop_live()
        self.pppp.handlers.remove(self._handler)
        del self._handler
        del self._tap

        app.svc.put("pppp")
