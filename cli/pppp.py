import time
import uuid
import logging as log

from datetime import datetime, timedelta
from tqdm import tqdm

import cli.util

from libflagship.pktdump import PacketWriter
from libflagship.pppp import Duid, P2PCmdType, FileTransfer
from libflagship.pppp import *
from libflagship.ppppapi import AnkerPPPPApi, PPPPState


def _pppp_dumpfile(api, dumpfile):
    if dumpfile:
        log.info(f"Logging all pppp traffic to {dumpfile!r}")
        pktwr = PacketWriter.open(dumpfile)
        api.set_dumper(pktwr)


def pppp_open(config, printer_index, timeout=None, dumpfile=None):
    if timeout:
        deadline = datetime.now() + timedelta(seconds=timeout)

    with config.open() as cfg:
        if printer_index >= len(cfg.printers):
            log.critical(f"Printer number {printer_index} out of range, max printer number is {len(cfg.printers)-1} ")
        printer = cfg.printers[printer_index]

        api = AnkerPPPPApi.open_lan(Duid.from_string(printer.p2p_duid), host=printer.ip_addr)
        _pppp_dumpfile(api, dumpfile)

        log.info(f"Trying connect to printer {printer.name} ({printer.p2p_duid}) over pppp using ip {printer.ip_addr}")

        api.connect_lan_search()
        api.start()

        while api.state != PPPPState.Connected:
            time.sleep(0.1)
            if api.stopped.is_set() or (timeout and (datetime.now() > deadline)):
                api.stop()
                raise ConnectionRefusedError("Connection rejected by device")

        log.info("Established pppp connection")
        return api


def pppp_open_broadcast(dumpfile=None):
    api = AnkerPPPPApi.open_broadcast()
    api.state = PPPPState.Connected
    _pppp_dumpfile(api, dumpfile)
    return api


def unique(items):
    seen = set()
    res = []
    for item in items:
        name = str(item)
        if name not in seen:
            res.append(item)
        seen.add(name)
    return res


def pppp_open_relay(env):
    with env.config.open() as cfg:
        printer = cfg.printers[0]

        key = printer.p2p_key.encode()
        duid = Duid.from_string(printer.p2p_duid)

        for host in printer.api_hosts[::-1]:
            print(host)

            try:
                api = AnkerPPPPApi.open_wan(duid, host=host)
                api.send(PktHello())
                helloack = api.recv()
                res = api.send(PktListReqDsk(duid=duid, dsk=Dsk(key=key)))

                relayto = api.recv(timeout=0.5)
                break
            except TimeoutError:
                continue
        else:
            log.critical("Could not reach any relay servers")

        relays = api.recv()
        relay = unique(relays.relays)[0]

        rel = AnkerPPPPApi.open(duid, relay.addr, relay.port)

        rel.send(PktRlyPkt(mark=relayto.mark, duid=duid, unk=0))
        rel.send(PktRlyHello())
        rel.recv()

        rel.send(PktRlyPort())
        rport = rel.recv()
        print(rport)

        api.send(PktRlyReq(duid=duid, host=Host(afam=2, port=rport.port, addr=relay.addr), mark=rport.mark))
        api.recv()
        rto = api.recv()

        rel2 = AnkerPPPPApi.open(duid, rto.host.addr, rto.host.port)
        rel2.send(PktRlyPkt(mark=rto.mark, duid=duid, unk=0))

        api.send(
            PktSessionReady(
                duid=duid, handle=2, max_handles=256, active_handles=2, startup_ticks=599,
                b1=0, b2=1, b3=126, b4=0,
                addr_local=Host(afam=2, port=32100, addr='FIXME'),
                addr_wan=helloack.host,
                addr_relay=Host(afam=2, addr=rel.addr[0], port=rto.host.port)
            )
        )

        api.recv()

        rel2.start()
        return rel2


def pppp_send_file(api, fui, data):
    log.info("Requesting file transfer..")
    api.send_xzyh(str(uuid.uuid4())[:16].encode(), cmd=P2PCmdType.P2P_SEND_FILE)

    log.info("Sending file metadata..")
    api.aabb_request(bytes(fui), frametype=FileTransfer.BEGIN)

    log.info("Sending file contents..")
    blocksize = 1024 * 32
    chunks = cli.util.split_chunks(data, blocksize)
    pos = 0

    with tqdm(unit="b", total=len(data), unit_scale=True, unit_divisor=1024) as bar:
        for chunk in chunks:
            api.aabb_request(chunk, frametype=FileTransfer.DATA, pos=pos)
            pos += len(chunk)
            bar.update(len(chunk))
