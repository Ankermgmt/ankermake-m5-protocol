import time
import uuid
import logging as log

from datetime import datetime, timedelta
from tqdm import tqdm

import cli.util

from libflagship.pktdump import PacketWriter
from libflagship.pppp import Duid, P2PCmdType, FileTransfer, PktLanSearch, PktPunchPkt
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


def pppp_find_printer_ip_addresses(dumpfile=None):
        # broadcast a search packet to all printers on the network
    api = pppp_open_broadcast(dumpfile=dumpfile)
    api.send(PktLanSearch())

    # collect replies from all available printers
    found_printers = dict()
    wait_time = 1.0      # wait 1.0 second for responses
    timeout = time.monotonic() + wait_time
    while wait_time > 0:
        try:
            resp = api.recv(timeout=wait_time)
        except TimeoutError:
            pass
        else:
            if isinstance(resp, PktPunchPkt):
                duid_str = str(resp.duid)
                found_printers[duid_str] = api.addr[0]
        wait_time = timeout - time.monotonic()

    return found_printers
