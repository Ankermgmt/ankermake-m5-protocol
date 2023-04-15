import json
import logging as log

from flask import Flask, request, render_template, Response
from flask_sock import Sock

from libflagship.util import enhex
from libflagship.pppp import P2PSubCmdType, P2PCmdType
from libflagship.ppppapi import FileUploadInfo, PPPPError, FileTransfer

from web.multiqueue import MultiQueue

import cli.mqtt


app = Flask(
    __name__,
    root_path=".",
    static_folder="static",
    template_folder="static"
)
app.config.from_prefixed_env()

sock = Sock(app)


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
        self.api = cli.pppp.pppp_open(app.config["config"], timeout=1, dumpfile=app.config.get("pppp_dump"))

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


@sock.route("/ws/ctrl")
def ctrl(sock):

    while True:
        msg = json.loads(sock.receive())

        if "light" in msg:
            app.videoq.send_command(
                P2PSubCmdType.LIGHT_STATE_SWITCH,
                data={"open": int(msg["light"])}
            )


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

    api = cli.pppp.pppp_open(config, dumpfile=app.config.get("pppp_dump"))

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


def webserver(config, host, port, **kwargs):
    app.config["config"] = config
    app.config["port"] = port
    app.config["host"] = host
    app.config.update(kwargs)
    app.run(host=host, port=port)
