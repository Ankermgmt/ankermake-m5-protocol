import uuid
import logging as log

from queue import Empty
from multiprocessing import Queue

from ..lib.service import Service
from .. import app

from libflagship.pppp import P2PCmdType, Aabb, FileTransfer, FileTransferReply
from libflagship.ppppapi import FileUploadInfo

import cli.util


class FileTransferService(Service):

    REPLY_TIMEOUT = 10.0

    def _tap_clear(self):
        try:
            while True:
                self._tap.get_nowait()
        except Empty:
            pass

    def api_aabb(self, api, frametype, msg=b"", pos=0):
        api.send_aabb(msg, frametype=frametype, pos=pos)

    def api_aabb_request(self, api, frametype, msg=b"", pos=0):
        self.api_aabb(api, frametype, msg, pos)
        try:
            resp = self._tap.get(timeout=self.REPLY_TIMEOUT)
        except Empty as e:
            raise ConnectionError("PPPP transfer timed out waiting for printer reply") from e

        log.debug(f"{self.name}: Aabb response: {resp}")

        if not isinstance(resp, Aabb):
            raise ConnectionError(f"Unexpected aabb response: {resp!r}")

        data = getattr(resp, "data", None)
        if not data or len(data) != 1:
            raise ConnectionError(f"Unexpected reply from printer: {data!r}")

        try:
            reply = FileTransferReply(data[0])
        except ValueError:
            raise ConnectionError(f"Unexpected transfer reply: 0x{data[0]:02x}") from None

        if reply != FileTransferReply.OK:
            raise ConnectionError(f"PPPP transfer failed: {reply.name}")

        return reply

    def send_file(self, fd, user_name, start_print=True):
        try:
            api = self.pppp._api
        except AttributeError:
            raise ConnectionError("No pppp connection to printer")

        data = fd.read()
        fui = FileUploadInfo.from_data(data, fd.filename, user_name=user_name, user_id="-", machine_id="-")
        log.info(f"Going to upload {fui.size} bytes as {fui.name!r}")
        try:
            self._tap_clear()

            log.info("Requesting file transfer..")
            api.send_xzyh(str(uuid.uuid4())[:16].encode(), cmd=P2PCmdType.P2P_SEND_FILE)

            log.info("Sending file metadata..")
            self.api_aabb_request(api, FileTransfer.BEGIN, bytes(fui))

            log.info("Sending file contents..")
            blocksize = 1024 * 32
            chunks = cli.util.split_chunks(data, blocksize)
            pos = 0

            for chunk in chunks:
                self.api_aabb_request(api, FileTransfer.DATA, chunk, pos)
                pos += len(chunk)

            if start_print:
                log.info("File upload complete. Requesting print start of job.")
                self.api_aabb_request(api, FileTransfer.END)
            else:
                log.info("File upload complete (upload-only)")
        except Exception as e:
            log.error(f"Could not send print job: {e}")
            raise
        else:
            if start_print:
                log.info("Successfully sent print job")
            else:
                log.info("Successfully uploaded file")

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
