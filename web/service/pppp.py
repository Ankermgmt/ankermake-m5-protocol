import json
import logging as log

from datetime import datetime, timedelta

from ..lib.service import Service, ServiceRestartSignal, ServiceStoppedError
from .. import app

from libflagship.pktdump import PacketWriter
from libflagship.pppp import P2PCmdType, PktClose, Duid, Type, Xzyh, Aabb
from libflagship.ppppapi import AnkerPPPPAsyncApi, PPPPState

import cli.pppp

class PPPPService(Service):

    def __init__(self):
        self.xzyh_handlers = []
        super().__init__()

    def api_command(self, commandType, **kwargs):
        if not hasattr(self, "_api"):
            raise ConnectionError("No pppp connection")
        cmd = {
            "commandType": commandType,
            **kwargs
        }
        return self._api.send_xzyh(
            json.dumps(cmd).encode(),
            cmd=P2PCmdType.P2P_JSON_CMD,
            block=False
        )

    def worker_start(self):
        config = app.config["config"]

        deadline = datetime.now() + timedelta(seconds=2)

        with config.open() as cfg:
            if not cfg:
                raise ServiceStoppedError("No config available")
            printer = cfg.printers[app.config["printer_index"]]

        ip_addr = cli.pppp.pppp_resolve_printer_ip(
            config,
            printer,
            app.config["printer_index"],
            dumpfile=app.config.get("pppp_dump"),
        )
        if not ip_addr:
            raise ConnectionRefusedError("No printer IP found; ensure printer is online on the same network")

        api = AnkerPPPPAsyncApi.open_lan(Duid.from_string(printer.p2p_duid), host=ip_addr)
        if app.config["pppp_dump"]:
            dumpfile = app.config["pppp_dump"]
            log.info(f"Logging all pppp traffic to {dumpfile!r}")
            pktwr = PacketWriter.open(dumpfile)
            api.set_dumper(pktwr)

        log.info(f"Trying connect to printer {printer.name} ({printer.p2p_duid}) over pppp using ip {ip_addr}")

        api.connect_lan_search()

        while api.state != PPPPState.Connected:
            try:
                msg = api.recv(timeout=(deadline - datetime.now()).total_seconds())
                api.process(msg)
            except StopIteration:
                raise ConnectionRefusedError("Connection rejected by device")

        log.info("Established pppp connection")
        self._api = api

    def _drain_xzyh(self, chan):
        if not hasattr(self, "_api") or not hasattr(self._api, "chans"):
            return

        if chan < 0 or chan >= len(self._api.chans):
            return

        fd = self._api.chans[chan]

        while True:
            with fd.lock:
                hdr = fd.peek(16, timeout=0.0)
                if not hdr:
                    return
                if hdr[:4] != b"XZYH":
                    return

                xzyh = Xzyh.parse(hdr)[0]
                pkt = fd.read(xzyh.len + 16, timeout=0.0)
                if not pkt:
                    return
                xzyh.data = pkt[16:]

            for handler in self.xzyh_handlers[:]:
                try:
                    handler((chan, xzyh))
                except Exception as e:
                    log.warning(f"Handler error: {e}")

    def _recv_aabb(self, fd):
        data = fd.read(12)
        aabb = Aabb.parse(data)[0]
        p = data + fd.read(aabb.len + 2)
        aabb, data = Aabb.parse_with_crc(p)[:2]
        return aabb, data

    def worker_run(self, timeout):
        try:
            msg = self._api.poll(timeout=timeout)
        except ConnectionResetError:
            raise ServiceRestartSignal()

        self._drain_xzyh(chan=1)

        if not msg or msg.type != Type.DRW:
            return

        ch = self._api.chans[msg.chan]

        drain_xzyh = False
        with ch.lock:
            header = ch.peek(4, timeout=0)
            if not header:
                return

            if header[:4] == b'XZYH':
                drain_xzyh = True
            elif header[:2] == b'\xAA\xBB':
                aabb_header = ch.peek(12, timeout=0)
                if not aabb_header:
                    return
                aabb = Aabb.parse(aabb_header)[0]
                frame_len = 12 + aabb.len + 2
                if not ch.peek(frame_len, timeout=0):
                    return

                aabb, data = self._recv_aabb(ch)
                if len(data) != 1:
                    raise ValueError(f"Unexpected reply from aabb request: {data}")

                aabb.data = data
                self.notify((msg.chan, aabb))
            else:
                raise ValueError(f"Unexpected data in stream: {header!r}")

        if drain_xzyh:
            self._drain_xzyh(chan=msg.chan)

    def worker_stop(self):
        self._api.send(PktClose())
        del self._api

    @property
    def connected(self):
        if not hasattr(self, "_api"):
            return False
        return self._api.state == PPPPState.Connected
