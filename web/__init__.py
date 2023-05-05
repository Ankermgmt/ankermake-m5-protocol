"""
This module is designed to implement a Flask web server for video streaming and downloading and other functionalities of AnkerMake M5. 
It also implements various services, routes and functions including, '/ws/mqtt', '/ws/video', 'ws/ctrl', '/video', '/' and '/reload'

Methods:
    - startup(): Registers required services on server start
    - shutdown(): Unregisters not required services on server shutdown
    - restart(): Shuts down and starts up the server to apply new changes

Routes:
    - /ws/mqtt: Handles receiving and sending messages on the 'mqttqueue' stream service through websocket
    - /ws/video: Handles receiving and sending messages on the 'videoqueue' stream service through websocket
    - /ws/ctrl: Handles controlling of light and video quality through websocket
    - /video: Handles the video streaming/downloading feature in the Flask app
    - /: Renders the html template for the root route, which is the homepage of the Flask app
    - /api/version: Returns the version details of api and server as dictionary
    - /api/web/config/upload: Handles the uploading of configuration file to Flask server and returns a HTML redirect response
    - /api/files/local: Handles the uploading of files to Flask server and returns a dictionary containing file details
    - /reload: Reloads the Flask server and returns a HTML redirect response

Functions:
    - webserver(config, host, port, **kwargs): Starts the Flask webserver
"""
import json
import logging as log
import traceback

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
    """
    Registers required services on server start
    """
    app.svc.register("pppp", web.service.pppp.PPPPService())
    app.svc.register("videoqueue", web.service.video.VideoQueue())
    app.svc.register("mqttqueue", web.service.mqtt.MqttQueue())
    app.svc.register("filetransfer", web.service.filetransfer.FileTransferService())


def shutdown():
    """
    Unregisters not required services on server shutdown
    """
    app.svc.unregister("pppp")
    app.svc.unregister("videoqueue")
    app.svc.unregister("mqttqueue")
    app.svc.unregister("filetransfer")


def restart():
    """
    Shuts down and starts up the server to apply new changes
    """
    shutdown()
    startup()


@sock.route("/ws/mqtt")
def mqtt(sock):
    """
    Handles receiving and sending messages on the 'mqttqueue' stream service through websocket
    """
    if not app.config["login"]:
        return
    for data in app.svc.stream("mqttqueue"):
        log.debug(f"MQTT message: {data}")
        sock.send(json.dumps(data))


@sock.route("/ws/video")
def video(sock):
    """
    Handles receiving and sending messages on the 'videoqueue' stream service through websocket
    """
    if not app.config["login"]:
        return
    for msg in app.svc.stream("videoqueue"):
        sock.send(msg.data)


@sock.route("/ws/ctrl")
def ctrl(sock):
    """
    Handles controlling of light and video quality through websocket
    """
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
    """
    Handles the video streaming/downloading feature in the Flask app
    """
    def generate():
        if not app.config["login"]:
            return
        for msg in app.svc.stream("videoqueue"):
            yield msg.data

    return Response(generate(), mimetype="video/mp4")


@app.get("/")
def app_root():
    """
    Renders the html template for the root route, which is the homepage of the Flask app
    """
    config = app.config["config"]
    with config.open() as cfg:
        user_agent = user_agent_parse(request.headers.get("User-Agent"))
        user_os = web.platform.os_platform(user_agent.os.family)

        host = request.host.split(":")
        # If there is no 2nd array entry, the request port is 80
        request_port = host[1] if len(host) > 1 else "80"
        if app.config["login"]:
            anker_config = str(web.config.config_show(cfg))
            printer_serial = str(cfg.printers[0].sn)
        else:
            anker_config = "<p>No printers found, please load your login config...</p>"
            printer_serial = None

        return render_template(
            "index.html",
            request_port=request_port,
            request_host=host[0],
            configure=app.config["login"],
            login_file_path=web.platform.login_path(user_os),
            anker_config=anker_config,
            printer_serial=printer_serial
        )


@app.get("/api/version")
def app_api_version():
    """
    Returns the version details of api and server as dictionary

    Returns:
        A dictionary containing version details of api and server
    """
    return {"api": "0.1", "server": "1.9.0", "text": "OctoPrint 1.9.0"}


@app.post("/api/web/config/upload")
def app_api_web_config_upload():
    """
    Handles the uploading of configuration file to Flask server

    Returns:
        A HTML redirect response
    """
    if request.method != "POST":
        return web.util.flash_redirect("/")
    if "login_file" not in request.files:
        return web.util.flash_redirect("/", "No file found", "danger")
    file = request.files["login_file"]

    try:
        web.config.config_import(file, app.config["config"])
        return web.util.flash_redirect("/reload", "AnkerMake Config Imported!", "success")
    except web.config.ConfigImportError as err:
        log.error(err)
        return web.util.flash_redirect("/", f"Error: {err}", "danger")
    except Exception as err:
        log.error(traceback.format_exc, err)
        return web.util.flash_redirect("/", f"Unexpected Error occurred: {err}", "danger")


@app.post("/api/files/local")
def app_api_files_local():
    """
    Handles the uploading of files to Flask server

    Returns:
        A dictionary containing file details
    """
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
    """
    Reloads the Flask server

    Returns:
        A HTML redirect response
    """
    config = app.config["config"]

    with config.open() as cfg:
        if not getattr(cfg, "printers", False):
            return web.util.flash_redirect("/", "No printers found in config", "warning")
        app.config["login"] = True
        session["_flashes"].clear()

        try:
            restart()
        except Exception as e:
            return web.util.flash_redirect("/", f"Ankerctl could not be reloaded: {e}", "danger")

        return web.util.flash_redirect("/", "Ankerctl reloaded successfully", "success")


def webserver(config, host, port, **kwargs):
    """
    Starts the Flask webserver

    Args:
        - config: A configuration object containing configuration information
        - host: A string containing host address to start the server
        - port: An integer specifying the port number of server
        - **kwargs: A dictionary containing additional configuration information

    Returns:
        - None
    """
    with config.open() as cfg:
        app.config["config"] = config
        app.config["login"] = True if cfg else False
        app.config["port"] = port
        app.config["host"] = host
        app.config.update(kwargs)
        app.run(host=host, port=port)
