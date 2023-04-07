import json
import atexit
import logging as log
import contextlib

from datetime import datetime, timedelta
from enum import Enum
from flask import Flask, request, render_template, Response
from flask_sock import Sock

from threading import Thread, Event
from multiprocessing import Queue

from libflagship.util import enhex
from libflagship.pppp import P2PSubCmdType, P2PCmdType
from libflagship.ppppapi import FileUploadInfo, PPPPError, FileTransfer

import cli.mqtt


app = Flask(
    __name__,
    static_folder="../static",
    template_folder="../static"
)
app.config.from_prefixed_env()

sock = Sock(app)


class RunState(Enum):
    Starting = 2
    Running  = 3
    # Idle     = 4
    Stopping = 5
    Stopped  = 6


class MultiQueue(Thread):

    def __init__(self, idle_timeout=10):
        super().__init__()
        self.timeout = timedelta(seconds=idle_timeout)
        self.running = True
        self.deadline = None
        self.state = RunState.Stopped
        self.wanted = False
        self.targets = []
        self._event = Event()
        atexit.register(self.atexit)
        super().start()

    def atexit(self):
        log.info(f"{self.name}: Requesting thread exit..")
        self.running = False
        self.join()
        log.info(f"{self.name}: Thread cleanup done")

    @property
    def name(self):
        return type(self).__name__

    def start(self):
        log.info(f"{self.name}: Requesting start")
        self.wanted = True
        self._event.set()

    def stop(self):
        log.info(f"{self.name}: Requesting stop")
        self.wanted = False
        self._event.set()

    def run(self):
        holdoff = None

        while self.running:
            if self.state == RunState.Starting:
                log.debug(f"{self.name}: {datetime.now()} vs holdoff {holdoff}")
                if datetime.now() > holdoff:
                    try:
                        log.info(f"{self.name} worker start")
                        self.worker_start()
                    except Exception as E:
                        log.error(f"{self.name}: Failed to start worker: {E}. Retrying in 1 second.")
                        holdoff = datetime.now() + timedelta(seconds=1)
                    else:
                        log.info(f"{self.name}: Worked started")
                        self.state = RunState.Running
                else:
                    self._event.wait(timeout=0.1)
                    self._event.clear()

            elif self.state == RunState.Running:
                if self.wanted:
                    self.worker_run(timeout=0.3)
                else:
                    log.info(f"{self.name}: Stopping worker")
                    holdoff = datetime.now()
                    self.state = RunState.Stopping

            elif self.state == RunState.Stopping:
                if datetime.now() > holdoff:
                    try:
                        self.worker_stop()
                    except Exception as E:
                        log.error(f"{self.name}: Failed to stop worker: {E}. Retrying in 1 second.")
                        holdoff = datetime.now() + timedelta(seconds=1)
                    else:
                        log.info(f"{self.name}: Worked stopped")
                        self.state = RunState.Stopped
                else:
                    self._event.wait(timeout=0.1)
                    self._event.clear()

            elif self.state == RunState.Stopped:
                if self.wanted:
                    log.info(f"{self.name}: Starting worker")
                    holdoff = datetime.now()
                    self.state = RunState.Starting
                else:
                    self._event.wait()
                    self._event.clear()
            else:
                raise ValueError("Unknown state value")

        log.info(f"{self.name}: Shutting down thread")
        if self.state == RunState.Running:
            self.worker_stop()
        log.info(f"{self.name}: Thread exit")

    def put(self, obj):
        for target in self.targets:
            target.put(obj)

    def add_target(self, target):
        if not self.targets:
            self.start()
        self.targets.append(target)

    def del_target(self, target):
        if target in self.targets:
            self.targets.remove(target)
            if not self.targets:
                self.stop()

    @contextlib.contextmanager
    def tap(self):
        queue = Queue()
        self.add_target(queue)
        yield queue
        self.del_target(queue)

    def worker_start(self):
        pass

    def worker_run(self, timeout):
        pass

    def worker_stop(self):
        pass


class MqttQueue(MultiQueue):

    def worker_start(self):
        self.client = cli.mqtt.mqtt_open(app.config["config"], True)

    def worker_run(self, timeout):
        for msg, body in self.client.fetch(timeout=timeout):
            log.info(f"TOPIC [{msg.topic}]")
            log.debug(enhex(msg.payload[:]))

            for obj in body:
                self.put(obj)

    def worker_stop(self):
        del self.client


class VideoQueue(MultiQueue):

    def send_command(self, commandType, **kwargs):
        cmd = {
            "commandType": commandType,
            **kwargs
        }
        return self.api.send_xzyh(
            json.dumps(cmd).encode(),
            cmd=P2PCmdType.P2P_JSON_CMD
        )

    def worker_start(self):
        self.api = cli.pppp.pppp_open(app.config["config"], timeout=1)

        self.send_command(P2PSubCmdType.START_LIVE, data={"encryptkey": "x", "accountId": "y"})

    def worker_run(self, timeout):
        d = self.api.recv_xzyh(chan=1, timeout=timeout)
        if not d:
            return

        log.debug(f"Video data packet: {enhex(d.data):32}...")
        self.put(d.data)

    def worked_stop(self):
        self.api.send_command(P2PSubCmdType.CLOSE_LIVE)


@app.before_first_request
def startup():
    app.mqttq = MqttQueue()
    app.videoq = VideoQueue()


@sock.route("/ws/mqtt")
def mqtt(sock):

    with app.mqttq.tap() as queue:
        while True:
            try:
                data = queue.get()
            except EOFError:
                break
            log.debug(f"MQTT message: {data}")
            sock.send(json.dumps(data))


@sock.route("/ws/video")
def video(sock):

    with app.videoq.tap() as queue:
        while True:
            try:
                data = queue.get()
            except EOFError:
                break
            sock.send(data)


@app.get("/video")
def video2():

    def generate():
        queue = Queue()
        app.videoq.add_target(queue)
        try:
            while True:
                try:
                    data = queue.get()
                except EOFError:
                    break
                yield data
        finally:
            app.videoq.del_target(queue)

    return Response(generate(), mimetype='video/mp4')


@app.get("/")
def app_root():
    host = request.host.split(':')
    requestPort = host[1] if len(host) > 1 else '80' # If there is no 2nd array entry, the request port is 80
    return render_template(
        "index.html",
        requestPort=requestPort,
        requestHost=host[0]
    )


@app.get("/api/version")
def app_api_version():
    return {
        "api": "0.1",
        "server": "1.9.0",
        "text": "OctoPrint 1.9.0"
    }


@app.post("/api/files/local")
def app_api_files_local():
    config = app.config["config"]

    user_name = request.headers.get("User-Agent", "ankerctl").split("/")[0]

    no_act = not cli.util.parse_http_bool(request.form["print"])

    if no_act:
        cli.util.http_abort(409, "Upload-only not supported by Ankermake M5")

    fd = request.files["file"]

    api = cli.pppp.pppp_open(config)

    data = fd.read()
    fui = FileUploadInfo.from_data(data, fd.filename, user_name=user_name, user_id="-", machine_id="-")
    log.info(f"Going to upload {fui.size} bytes as {fui.name!r}")
    try:
        cli.pppp.pppp_send_file(api, fui, data)
        log.info("File upload complete. Requesting print start of job.")
        api.aabb_request(b"", frametype=FileTransfer.END)
    except PPPPError as E:
        log.error(f"Could not send print job: {E}")
    else:
        log.info("Successfully sent print job")
    finally:
        api.stop()

    return {}


def webserver(config, host, port):
    app.config["config"] = config
    app.config["port"] = port
    app.config["host"] = host
    app.run(host=host, port=port)
