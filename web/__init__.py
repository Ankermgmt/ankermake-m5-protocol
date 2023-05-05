import json
import logging as log

from secrets import token_urlsafe as token
from flask import Flask, request, render_template, Response, session, url_for
from flask_sock import Sock
from user_agents import parse as user_agent_parse

from web.lib.service import ServiceManager

import web.config
import web.platform
import web.util

import cli.util
import cli.config


app = Flask(__name__, root_path=".", static_folder="static", template_folder="static")
# secret_key is required for flash() to function
app.secret_key = token(24)
app.config.from_prefixed_env()
app.svc = ServiceManager()

sock = Sock(app)


# autopep8: off
import web.service.pppp
import web.service.video
import web.service.mqtt
import web.service.filetransfer
# autopep8: on


@app.before_first_request
def startup():
    app.svc.register("pppp", web.service.pppp.PPPPService())
    app.svc.register("videoqueue", web.service.video.VideoQueue())
    app.svc.register("mqttqueue", web.service.mqtt.MqttQueue())
    app.svc.register("filetransfer", web.service.filetransfer.FileTransferService())


def shutdown():
    app.svc.unregister("pppp")
    app.svc.unregister("videoqueue")
    app.svc.unregister("mqttqueue")
    app.svc.unregister("filetransfer")


def restart():
    shutdown()
    startup()


@sock.route("/ws/mqtt")
def mqtt(sock):
    if not app.config["login"]:
        return
    for data in app.svc.stream("mqttqueue"):
        log.debug(f"MQTT message: {data}")
        sock.send(json.dumps(data))


@sock.route("/ws/video")
def video(sock):
    if not app.config["login"]:
        return
    for msg in app.svc.stream("videoqueue"):
        sock.send(msg.data)


@sock.route("/ws/ctrl")
def ctrl(sock):
    if not app.config["login"]:
        return
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
        if not app.config["login"]:
            return
        for msg in app.svc.stream("videoqueue"):
            yield msg.data

    return Response(generate(), mimetype="video/mp4")


@app.get("/")
def app_root():
    config = app.config["config"]
    with config.open() as cfg:
        user_agent = user_agent_parse(request.headers.get("User-Agent"))

        host = request.host.split(":")
        # If there is no 2nd array entry, the request port is 80
        request_port = host[1] if len(host) > 1 else "80"
        no_config = "<p>No printers found, please load your login config...</p>"
        anker_config = (
            str(web.config.config_show(cfg)) if app.config["login"] else no_config
        )

        return render_template(
            "index.html",
            request_port=request_port,
            request_host=host[0],
            configure=app.config["login"],
            login_file_path=web.platform.login_path(
                web.platform.os_platform(user_agent.os.family)
            ),
            anker_config=anker_config,
        )


@app.get("/api/version")
def app_api_version():
    return {"api": "0.1", "server": "1.9.0", "text": "OctoPrint 1.9.0"}


@app.post("/api/web/config/upload")
def app_api_web_config_upload():
    if request.method != "POST":
        return web.util.flash_redirect("/")
    if "login_file" not in request.files:
        return web.util.flash_redirect("/", "No file found", "danger")
    file = request.files["login_file"]

    try:
        web.config.config_import(file, app.config["config"])
        return web.util.flash_redirect("/reload", "AnkerMake Config Imported!", "success")
    except web.config.ConfigAPIError as e:
        log.error(e)
        return web.util.flash_redirect("/", f"Error: {e}", "danger")
    except Exception as e:
        log.error(traceback.format_exc)
        return web.util.flash_redirect("/", f"Unexpected Error occurred: {e}", "danger")


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


@app.get("/reload")
def reload_webserver():
    config = app.config["config"]

    with config.open() as cfg:
        if not getattr(cfg, "printers", False):
            return web.util.flash_redirect("/", "No printers found in config", "warning")
        app.config["login"] = True
        session["_flashes"].clear()

        try:
            restart()
        except Exception as e:
            return web.util.flash_redirect("/", f"Anerctl could not be reloaded: {e}", "danger")

        return web.util.flash_redirect("/", "Anerctl reloaded successfully", "success")


def webserver(config, host, port, **kwargs):
    with config.open() as cfg:
        app.config["config"] = config
        app.config["login"] = True if cfg else False
        app.config["port"] = port
        app.config["host"] = host
        app.config.update(kwargs)
        app.run(host=host, port=port)
