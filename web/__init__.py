import json
import logging as log

from flask import Flask, request, render_template
from flask_sock import Sock

from threading import Thread
from multiprocessing import Queue

from libflagship.util import enhex
from libflagship.ppppapi import FileUploadInfo, PPPPError, FileTransfer

import cli.mqtt


app = Flask(
    __name__,
    static_folder="../static",
    template_folder="../static"
)
app.config.from_prefixed_env()

sock = Sock(app)


class MqttQueue(Thread):

    def __init__(self):
        super().__init__()
        self.targets = []
        self.client = cli.mqtt.mqtt_open(app.config["config"], True)

    def run(self):
        client = self.client
        for msg, body in client.fetchloop():
            log.info(f"TOPIC [{msg.topic}]")
            log.debug(enhex(msg.payload[:]))

            for obj in body:
                for target in self.targets:
                    target.put(obj)

    def add_target(self, target):
        self.targets.append(target)

    def del_target(self, target):
        if target in self.targets:
            self.targets.remove(target)


@app.before_first_request
def startup():
    app.mqttq = MqttQueue()
    app.mqttq.start()


@sock.route("/mqtt")
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
