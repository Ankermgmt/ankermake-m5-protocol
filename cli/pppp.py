import time
import logging as log

from libflagship.pppp import P2PSubCmdType, PktLanSearch, Duid, P2PCmdType
from libflagship.ppppapi import AnkerPPPPApi, FileTransfer, FileUploadInfo


def pppp_open(env):
    with env.config.open() as cfg:
        printer = cfg.printers[0]

        api = AnkerPPPPApi.open_lan(Duid.from_string(printer.p2p_duid), host=printer.ip_addr)
        log.info("Trying connect over pppp")
        api.start()

        api.send(PktLanSearch())

        while not api.rdy:
            time.sleep(0.1)

        log.info("Established pppp connection")
        return api
