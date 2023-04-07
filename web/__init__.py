import json
import logging as log

from flask import Flask, request, render_template
from flask_sock import Sock

from threading import Thread
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


class MultiQueue(Thread):

    def __init__(self):
        super().__init__()
        self.running = False
        self.targets = []

    def start(self):
        self.running = True
        super().start()

    def stop(self):
        self.running = False
        self.join()

    def put(self, obj):
        for target in self.targets:
            target.put(obj)

    def add_target(self, target):
        if not self.running:
            self.start()
        self.targets.append(target)

    def del_target(self, target):
        if target in self.targets:
            self.targets.remove(target)
        if not self.targets and self.running:
            self.stop()


class MqttQueue(MultiQueue):

    def run(self):
        client = cli.mqtt.mqtt_open(app.config["config"], True)
        while self.running:
            for msg, body in client.fetch(timeout=0.5):
                log.info(f"TOPIC [{msg.topic}]")
                log.debug(enhex(msg.payload[:]))

                for obj in body:
                    self.put(obj)


class VideoQueue(MultiQueue):

    def __init__(self):
        super().__init__()

    def run(self):
        api = cli.pppp.pppp_open(app.config["config"])
        cmd = {"commandType": P2PSubCmdType.START_LIVE, "data": {"encryptkey": "x", "accountId": "y"}}
        api.send_xzyh(json.dumps(cmd).encode(), cmd=P2PCmdType.P2P_JSON_CMD)

        try:
            while self.running:
                d = api.recv_xzyh(chan=1)
                log.debug(f"Video data packet: {enhex(d.data):32}...")
                self.put(d.data)
        finally:
            cmd = {"commandType": P2PSubCmdType.CLOSE_LIVE}
            api.send_xzyh(json.dumps(cmd).encode(), cmd=P2PCmdType.P2P_JSON_CMD)


@app.before_first_request
def startup():
    app.mqttq = MqttQueue()
    app.videoq = VideoQueue()


@sock.route("/ws/mqtt")
def mqtt(sock):

    queue = Queue()
    app.mqttq.add_target(queue)
    try:
        while True:
            data = queue.get()
            log.debug(f"MQTT message: {data}")
            sock.send(json.dumps(data))
    finally:
        app.mqttq.del_target(queue)


@sock.route("/ws/video")
def video(sock):
    queue = Queue()
    app.videoq.add_target(queue)
    try:
        while True:
            data = queue.get()
            sock.send(data)
    finally:
        app.videoq.del_target(queue)


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
