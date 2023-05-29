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
import logging as log

from secrets import token_urlsafe as token
from flask import Flask
from flask_cors import CORS

from libflagship import ROOT_DIR

from web.lib.service import ServiceManager

import web.config
import web.platform
import web.util
import web.rpcutil
import web.moonraker
import web.moonraker.server

import web.service.pppp
import web.service.video
import web.service.mqtt
import web.service.filetransfer
import web.service.updates
import web.service.jobqueue


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
        import web.base
        import web.api.ws
        import web.api.ankerctl
        import web.api.octoprint

        app = Flask(__name__, root_path=ROOT_DIR, static_folder="static", template_folder="static")

        # secret_key is required for flash() to function
        app.secret_key = token(24)
        app.config.from_prefixed_env()
        app.svc = ServiceManager()

        # Register CORS handler for rpc endpoints, to allow mainsail to accept files and
        # resources from ankerctl.
        app.cors = CORS(
            app,
            resources={
                r"/server/*": {"origins": "*"},
                r"/video/*": {"origins": "*"},
            }
        )

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
        app.svc.register("updates", web.service.updates.UpdateNotifierService(app))
        app.svc.register("jobqueue", web.service.jobqueue.JobQueueService(app))

        # Take a reference to the "updates" service to make it run at all
        # times. This ensures that we can track temperatures and other state,
        # even when no clients are actively connected.
        #
        # One downside of this, is that the "mqttqueue" service will always be
        # activated, since the "updates" service depends on it. However, unlike
        # most of the other services, mqtt supports multiple clients, so this
        # will not prevent any other programs from using the printer.
        app.svc.get("updates")

        app.register_blueprint(web.moonraker.server.router, url_prefix="/server")
        app.register_blueprint(web.api.ws.router, url_prefix="/ws")
        app.register_blueprint(web.api.octoprint.router, url_prefix="/api")
        app.register_blueprint(web.api.ankerctl.router, url_prefix="/api/ankerctl")
        app.register_blueprint(web.base.router, url_prefix="/")

        app.run(host=host, port=port)
