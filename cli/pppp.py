import time
import uuid
import click
import logging as log

from tqdm import tqdm

import cli.util

from libflagship.pppp import PktLanSearch, Duid, P2PCmdType
from libflagship.ppppapi import AnkerPPPPApi, FileTransfer


def pppp_open(config):
    with config.open() as cfg:
        printer = cfg.printers[0]

        api = AnkerPPPPApi.open_lan(Duid.from_string(printer.p2p_duid), host=printer.ip_addr)
        log.info("Trying connect over pppp")
        api.daemon = True
        api.start()

        api.send(PktLanSearch())

        while not api.rdy:
            time.sleep(0.1)

        log.info("Established pppp connection")
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
