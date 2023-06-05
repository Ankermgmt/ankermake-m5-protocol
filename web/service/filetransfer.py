import uuid
import logging as log

from multiprocessing import Queue
from queue import Empty

from ..lib.service import Service

from libflagship.pppp import P2PCmdType, Aabb, FileTransfer, FileTransferReply
from libflagship.ppppapi import FileUploadInfo, PPPPError

import cli.mqtt
import cli.util


class FileTransferService(Service):

    def api_aabb(self, api, frametype, msg=b"", pos=0):
        api.send_aabb(msg, frametype=frametype, pos=pos)

    def api_aabb_request(self, api, frametype, msg=b"", pos=0):
        self.api_aabb(api, frametype, msg, pos)
        resp = self._tap.get(timeout=4)
        res = FileTransferReply(resp.data[0])
        log.debug(f"{self.name}: Aabb response: {resp} {res}")
        if res != FileTransferReply.OK:
            raise PPPPError(res, f"File transfer error: {res.name}")

    def send_file(self, fd, user_name):
        try:
            api = self.pppp._api
        except AttributeError:
            raise ConnectionError("No pppp connection to printer")

        umgr = self.upd.umgr

        data = fd.read()
        fui = FileUploadInfo.from_data(data, fd.filename, user_name=user_name, user_id="-", machine_id="-")
        log.info(f"Going to upload {fui.size} bytes as {fui.name!r}")

        self.jq.history_start()

        umgr.print_stats.filename = fd.filename
        umgr.print_stats.state = "Starting upload.."
        try:
            log.info("Requesting file transfer..")
            api.send_xzyh(str(uuid.uuid4())[:16].encode(), cmd=P2PCmdType.P2P_SEND_FILE)

            log.info("Sending file metadata..")
            self.api_aabb_request(api, FileTransfer.BEGIN, bytes(fui) + b"\x00")

            log.info("Sending file contents..")
            blocksize = 1024 * 32
            chunks = cli.util.split_chunks(data, blocksize)
            pos = 0

            for chunk in chunks:
                self.api_aabb_request(api, FileTransfer.DATA, chunk, pos)
                pos += len(chunk)
                umgr.print_stats.state = f"Uploading [{(pos / len(data))*100.0:.2f}%]"
                umgr.display_status.message = f"Uploading {pos} of {len(data)}"

            log.info("File upload complete. Requesting print start of job.")

            self.api_aabb_request(api, FileTransfer.END)

        except Exception as e:
            if isinstance(e, Empty):
                e = PPPPError(FileTransferReply.ERR_TIMEOUT, "File transfer timeout")
            desc = str(e) or repr(e)
            log.error(f"Could not send print job: {desc}")
            umgr.print_stats.state = "ready"
            umgr.print_stats.filename = None
            umgr.display_status.message = desc
            self.jq.history_error()
            raise

        else:
            self.jq.history_status("in_progress")
            umgr.print_stats.state = "Starting print.."
            umgr.display_status.message = None
            log.info("Successfully sent print job")

    def handler(self, data):
        chan, msg = data
        if isinstance(msg, Aabb):
            self._tap.put(msg)

    def worker_start(self):
        self.pppp = self.app.svc.get("pppp")
        self.upd  = self.app.svc.get("updates")
        self.jq   = self.app.svc.get("jobqueue")
        self._tap = Queue()

        self.pppp.handlers.append(self.handler)

    def worker_run(self, timeout):
        self.idle(timeout=timeout)

    def worker_stop(self):
        self.pppp.handlers.remove(self.handler)
        del self._tap

        self.app.svc.put("jobqueue")
        self.app.svc.put("updates")
        self.app.svc.put("pppp")
