import time
import click
import logging as log

from libflagship.pppp import PktLanSearch, Duid, P2PCmdType
from libflagship.ppppapi import AnkerPPPPApi, FileTransfer


def pppp_open(env):
    with env.config.open() as cfg:
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
    api.send_xzyh(b"12345678-1234-12", cmd=P2PCmdType.P2P_SEND_FILE)

    log.info("Sending file metadata..")
    api.aabb_request(bytes(fui), frametype=FileTransfer.BEGIN)

    log.info("Sending file contents..")
    ack1, ack2 = api.send_aabb(data, frametype=FileTransfer.DATA, block=False)

    last = ack1
    with click.progressbar(length=ack2 - ack1, label="File upload") as bar:
        chan = api.chans[1]
        while True:
            chan.wait()
            bar.update(chan.tx_ack - last, current_item=chan.tx_ack)
            last = chan.tx_ack
            if chan.tx_ack >= ack2:
                break
        bar.pos = ack2
        bar.render_progress()

    api.recv_aabb_reply()

    log.info("Completing file upload")
    api.aabb_request(b"", frametype=FileTransfer.END)
