import struct

from ..lib.service import Service, ServiceRestartSignal
from .. import app

from libflagship.pppp import P2PCmdType, Xzyh


class VideoControl(Service):

    def _handler(self, data):
        chan, msg = data

        if chan != 2:
            return

        if not isinstance(msg, Xzyh):
            return

        if msg.cmd == P2PCmdType.APP_CMD_WIFI_CONFIG:
            self.notify({
                "wifi": struct.unpack("<Q", msg.data)[0]
            })

    def worker_start(self):
        self.pppp = app.svc.get("pppp")

        self.api_id = id(self.pppp._api)

        self.pppp.handlers.append(self._handler)

    def worker_run(self, timeout):
        self.idle(timeout=timeout)

        if not self.pppp.connected:
            raise ServiceRestartSignal("No pppp connection")

        if id(self.pppp._api) != self.api_id:
            raise ServiceRestartSignal("New pppp connection detected, restarting video feed")

    def worker_stop(self):
        self.pppp.handlers.remove(self._handler)

        app.svc.put("pppp")
