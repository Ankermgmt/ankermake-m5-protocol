import json
import logging as log

from flask import Flask, request, render_template, Response
from flask_sock import Sock

from libflagship.pppp import P2PSubCmdType, FileTransfer
from libflagship.ppppapi import FileUploadInfo, PPPPError


from web.lib.service import ServiceManager

import cli.util

app = Flask(
    __name__,
    root_path=".",
    static_folder="static",
    template_folder="static"
)
app.config.from_prefixed_env()
app.svc = ServiceManager()

sock = Sock(app)


import web.service.pppp
import web.service.video
import web.service.mqtt
import web.service.filetransfer


@app.before_first_request
def startup():
    app.svc.register("pppp", web.service.pppp.PPPPService())
    app.svc.register("videoqueue", web.service.video.VideoQueue())
    app.svc.register("mqttqueue", web.service.mqtt.MqttQueue())
    app.svc.register("filetransfer", web.service.filetransfer.FileTransferService())


@sock.route("/ws/mqtt")
def mqtt(sock):

    for data in app.svc.stream("mqttqueue"):
        log.debug(f"MQTT message: {data}")
        sock.send(json.dumps(data))


@sock.route("/ws/video")
def video(sock):

    for msg in app.svc.stream("videoqueue"):
        sock.send(msg.data)


@sock.route("/ws/ctrl")
def ctrl(sock):

    while True:
        msg = json.loads(sock.receive())

        if "light" in msg:
            with app.svc.borrow("videoqueue") as vq:
                vq.api_light_state(msg["light"])

        if "quality" in msg:
            with app.svc.borrow("videoqueue") as vq:
                vq.api_video_mode(msg["quality"])


@app.get("/video")
def video_download():

    def generate():
        for msg in app.svc.stream("videoqueue"):
            yield msg.data

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
    user_name = request.headers.get("User-Agent", "ankerctl").split("/")[0]

    no_act = not cli.util.parse_http_bool(request.form["print"])

    if no_act:
        cli.util.http_abort(409, "Upload-only not supported by Ankermake M5")

    fd = request.files["file"]

    with app.svc.borrow("filetransfer") as ft:
        ft.send_file(fd, user_name)

    return {}


def webserver(config, host, port, **kwargs):
    app.config["config"] = config
    app.config["port"] = port
    app.config["host"] = host
    app.config.update(kwargs)
    app.run(host=host, port=port)
