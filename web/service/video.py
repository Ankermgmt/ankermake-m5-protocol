import json
import logging
import time

from queue import Empty
from multiprocessing import Queue

log = logging.getLogger(__name__)

from ..lib.service import Service, ServiceRestartSignal, RunState
from .. import app

from libflagship.pppp import P2PSubCmdType, P2PCmdType, Xzyh


VIDEO_PROFILES = [
    {
        "id": "sd",
        "label": "SD",
        "display": "SD (848x480)",
        "width": 848,
        "height": 480,
        "live": True,
        "live_mode": 0,
    },
    {
        "id": "hd",
        "label": "HD",
        "display": "HD (720p)",
        "width": 1280,
        "height": 720,
        "live": True,
        "live_mode": 1,
    },
    {
        "id": "fhd",
        "label": "FHD",
        "display": "FHD (1080p) - snapshot only",
        "width": 1920,
        "height": 1080,
        "live": False,
        "live_mode": None,
    },
]

VIDEO_PROFILES_BY_ID = {profile["id"]: profile for profile in VIDEO_PROFILES}
VIDEO_PROFILES_BY_MODE = {
    profile["live_mode"]: profile
    for profile in VIDEO_PROFILES
    if profile.get("live_mode") is not None
}
VIDEO_PROFILE_DEFAULT_ID = "hd" if "hd" in VIDEO_PROFILES_BY_ID else VIDEO_PROFILES[0]["id"]


class VideoQueue(Service):
    def __init__(self):
        self.video_enabled = False
        self.last_frame_at = None
        self._enable_generation = 0  # increments each time video is enabled
        super().__init__()

    def api_start_live(self):
        self.pppp.api_command(P2PSubCmdType.START_LIVE, data={
            "encryptkey": "x",
            "accountId": "y",
        })

    def api_stop_live(self):
        self.pppp.api_command(P2PSubCmdType.CLOSE_LIVE)

    def api_light_state(self, light):
        self.saved_light_state = light  # Track desired state regardless of connection
        if not self.pppp:
            return False
        self.pppp.api_command(P2PSubCmdType.LIGHT_STATE_SWITCH, data={
            "open": light,
        })
        log.info(f"VideoQueue: light {'on' if light else 'off'}")
        return True

    def api_video_mode(self, mode):
        try:
            mode = int(mode)
        except (TypeError, ValueError):
            log.warning(f"{self.name}: Invalid video mode {mode!r}")
            return False
        self.saved_video_mode = mode
        profile = VIDEO_PROFILES_BY_MODE.get(mode)
        if profile:
            self.saved_video_profile_id = profile["id"]
        if not self.pppp:
            return False
        self.pppp.api_command(P2PSubCmdType.LIVE_MODE_SET, data={"mode": mode})
        return True

    def api_video_profile(self, profile_id):
        if profile_id is None:
            return False
        profile_key = str(profile_id).lower()
        profile = VIDEO_PROFILES_BY_ID.get(profile_key)
        if not profile:
            log.warning(f"{self.name}: Unknown video profile {profile_id!r}")
            return False
        self.saved_video_profile_id = profile["id"]
        live_mode = profile.get("live_mode")
        if not profile.get("live") or live_mode is None:
            log.info(f"{self.name}: Video profile {profile_id!r} is not supported for live view")
            return False
        self.saved_video_mode = live_mode
        if not self.pppp:
            return True
        self.pppp.api_command(P2PSubCmdType.LIVE_MODE_SET, data={"mode": live_mode})
        return True

    def _handler(self, data):
        chan, msg = data

        if chan != 1:
            return

        if not isinstance(msg, Xzyh):
            return

        if msg.cmd == P2PCmdType.APP_CMD_VIDEO_FRAME:
            self.last_frame_at = time.monotonic()

        self.notify(msg)

    def worker_init(self):
        self.saved_light_state = None
        self.saved_video_mode = None
        self.saved_video_profile_id = None
        self.last_frame_at = None
        self.pppp = None

    def worker_start(self):
        if not self.video_enabled:
            return
        self.pppp = app.svc.get("pppp")

        self.api_id = id(self.pppp._api)

        self.pppp.xzyh_handlers.append(self._handler)

        self.api_start_live()

        if self.saved_light_state is not None:
            self.api_light_state(self.saved_light_state)

        if self.saved_video_profile_id is not None:
            applied = self.api_video_profile(self.saved_video_profile_id)
            if not applied and self.saved_video_mode is not None:
                self.api_video_mode(self.saved_video_mode)
        elif self.saved_video_mode is not None:
            self.api_video_mode(self.saved_video_mode)

    def worker_run(self, timeout):
        if not self.video_enabled:
            return
        self.idle(timeout=timeout)

        if not self.pppp.connected:
            raise ServiceRestartSignal("No pppp connection")

        if id(self.pppp._api) != self.api_id:
            raise ServiceRestartSignal("New pppp connection detected, restarting video feed")

    def worker_stop(self):
        try:
            self.api_stop_live()
        except Exception as E:
            log.warning(f"{self.name}: Failed to send stop command ({E})")

        if self.pppp and self._handler in self.pppp.xzyh_handlers:
            self.pppp.xzyh_handlers.remove(self._handler)

        if self.pppp:
            app.svc.put("pppp")
            self.pppp = None

    def set_video_enabled(self, enabled):
        if enabled == self.video_enabled:
            return True

        self.video_enabled = enabled
        if not enabled:
            self.last_frame_at = None
        if enabled:
            self._enable_generation += 1
            if self.state == RunState.Stopped:
                self.start()
        else:
            if self.state == RunState.Running:
                self.stop()
        return True
