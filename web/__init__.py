"""
This module is designed to implement a Flask web server for video
streaming and handling other functionalities of AnkerMake M5.
It also implements various services, routes and functions including.

Methods:
    - startup(): Registers required services on server start

Routes:
    - /ws/mqtt: Handles receiving and sending messages on the 'mqttqueue' stream service through websocket
    - /ws/video: Handles receiving and sending messages on the 'videoqueue' stream service through websocket
    - /ws/ctrl: Handles controlling of light and video quality through websocket
    - /video: Handles the video streaming/downloading feature in the Flask app
    - /: Renders the html template for the root route, which is the homepage of the Flask app
    - /api/version: Returns the version details of api and server as dictionary
    - /api/ankerctl/config/upload: Handles the uploading of configuration file \
        to Flask server and returns a HTML redirect response
    - /api/ankerctl/server/reload: Reloads the Flask server and returns a HTML redirect response
    - /api/files/local: Handles the uploading of files to Flask server and returns a dictionary containing file details

Functions:
    - webserver(config, host, port, **kwargs): Starts the Flask webserver

Services:
    - util: Houses utility services for use in the web module
    - config: Handles configuration manipulation for ankerctl
"""
import json
import logging as log

from secrets import token_urlsafe as token
from flask import Flask, request, render_template, Response, url_for
from flask_sock import Sock
from flask_cors import CORS
from user_agents import parse as user_agent_parse
from jsonrpc import JSONRPCResponseManager, dispatcher

from libflagship import ROOT_DIR

from web.lib.service import ServiceManager

import web.config
import web.platform
import web.util
import web.rpcutil
import web.moonraker
import web.moonraker.server

import cli.util
import cli.config


app = Flask(__name__, root_path=ROOT_DIR, static_folder="static", template_folder="static")
# secret_key is required for flash() to function
app.secret_key = token(24)
app.config.from_prefixed_env()
app.svc = ServiceManager()

sock = Sock(app)

# Register CORS handler for rpc endpoints, to allow mainsail to accept files and
# resources from ankerctl.
cors = CORS(
    app,
    resources={
        r"/server/*": {"origins": "*"},
        r"/video/*": {"origins": "*"},
    }
)


# autopep8: off
import web.service.pppp
import web.service.video
import web.service.mqtt
import web.service.filetransfer
import web.service.mqttnotifier
# autopep8: on


@sock.route("/websocket")
def websocket(sock):
    with app.svc.borrow("mqttnotifier") as notifier:
        with notifier.tap(lambda data: sock.send(data)):
            while True:
                msg = sock.receive()
                response = JSONRPCResponseManager.handle(msg, dispatcher)
                jmsg = json.loads(msg)
                web.rpcutil.log_jsonrpc_req(jmsg, response)
                sock.send(response.json)


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

        if cfg:
            anker_config = str(web.config.config_show(cfg))
            printer = cfg.printers[app.config["printer_index"]]
        else:
            anker_config = "No printers found, please load your login config..."
            printer = None

        if ":" in request.host:
            request_host, request_port = request.host.split(":", 1)
        else:
            request_host = request.host
            request_port = "80"

        return render_template(
            "index.html",
            request_host=request_host,
            request_port=request_port,
            configure=app.config["login"],
            login_file_path=web.platform.login_path(user_os),
            anker_config=anker_config,
            printer=printer
        )


def webserver(config, printer_index, host, port, insecure=False, **kwargs):
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
        import web.moonraker.server
        import web.api.ws
        import web.api.ankerctl
        import web.api.octoprint

        if cfg and printer_index >= len(cfg.printers):
            log.critical(f"Printer number {printer_index} out of range, max printer number is {len(cfg.printers)-1} ")
        app.config["config"] = config
        app.config["login"] = bool(cfg)
        app.config["printer_index"] = printer_index
        app.config["port"] = port
        app.config["host"] = host
        app.config["insecure"] = insecure
        app.config.update(kwargs)
        app.svc.register("pppp", web.service.pppp.PPPPService(app))
        app.svc.register("videoqueue", web.service.video.VideoQueue(app))
        app.svc.register("mqttqueue", web.service.mqtt.MqttQueue(app))
        app.svc.register("filetransfer", web.service.filetransfer.FileTransferService(app))
        app.svc.register("mqttnotifier", web.service.mqttnotifier.MqttNotifierService(app))
        app.websockets = []
        app.heater_target = 0.0
        app.hotbed_target = 0.0

        app.register_blueprint(web.moonraker.server.router, url_prefix="/server")
        app.register_blueprint(web.api.ws.router, url_prefix="/ws")
        app.register_blueprint(web.api.octoprint.router, url_prefix="/api")
        app.register_blueprint(web.api.ankerctl.router, url_prefix="/api/ankerctl")

        app.run(host=host, port=port)
