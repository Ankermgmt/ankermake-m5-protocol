import uuid
import logging as log

from multiprocessing import Queue

from ..lib.service import Service
from .. import app

from libflagship.pppp import P2PCmdType, Aabb, FileTransfer
from libflagship.ppppapi import FileUploadInfo, PPPPError

import cli.mqtt
import cli.util


class FileTransferService(Service):

    def api_aabb(self, api, frametype, msg=b"", pos=0):
        api.send_aabb(msg, frametype=frametype, pos=pos)

    def api_aabb_request(self, api, frametype, msg=b"", pos=0):
        self.api_aabb(api, frametype, msg, pos)
        resp = self._tap.get()
        log.debug(f"{self.name}: Aabb response: {resp}")

    def send_file(self, fd, user_name):
        api = self.pppp._api
        data = fd.read()
        fui = FileUploadInfo.from_data(data, fd.filename, user_name=user_name, user_id="-", machine_id="-")
        log.info(f"Going to upload {fui.size} bytes as {fui.name!r}")
        try:
            log.info("Requesting file transfer..")
            api.send_xzyh(str(uuid.uuid4())[:16].encode(), cmd=P2PCmdType.P2P_SEND_FILE)

            log.info("Sending file metadata..")
            self.api_aabb(api, FileTransfer.BEGIN, bytes(fui) + b"\x00")

            log.info("Sending file contents..")
            blocksize = 1024 * 32
            chunks = cli.util.split_chunks(data, blocksize)
            pos = 0

            for chunk in chunks:
                self.api_aabb_request(api, FileTransfer.DATA, chunk, pos)
                pos += len(chunk)

            log.info("File upload complete. Requesting print start of job.")

            self.api_aabb_request(api, FileTransfer.END)
        except PPPPError as E:
            log.error(f"Could not send print job: {E}")
        else:
            log.info("Successfully sent print job")

    def handler(self, data):
        chan, msg = data
        if isinstance(msg, Aabb):
            self._tap.put(msg)

    def worker_start(self):
        self.pppp = app.svc.get("pppp")
        self._tap = Queue()

        self.pppp.handlers.append(self.handler)

    def worker_run(self, timeout):
        self.idle(timeout=timeout)

    def worker_stop(self):
        self.pppp.handlers.remove(self.handler)
        del self._tap

        app.svc.put("pppp")
