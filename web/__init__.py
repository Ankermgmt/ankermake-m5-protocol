"""
This module is designed to implement a Flask web server for video
streaming and handling other functionalities of AnkerMake M5.
It also implements various services, routes and functions including.

Methods:
    - startup(): Registers required services on server start

Routes:
    - /ws/mqtt: Handles receiving and sending messages on the 'mqttqueue' stream service through websocket
    - /ws/pppp-state: Provides the status of the 'pppp' stream service through websocket
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
import os
import time

from secrets import token_urlsafe as token
from flask import Flask, flash, request, render_template, Response, session, url_for
from flask_sock import Sock
from simple_websocket.errors import ConnectionClosed
from user_agents import parse as user_agent_parse

from libflagship import ROOT_DIR
from libflagship.notifications import AppriseClient

from web.lib.service import ServiceManager, RunState, ServiceStoppedError

import web.config
import web.platform
import web.util

import cli.util
import cli.config
from cli.model import (
    UPLOAD_RATE_MBPS_CHOICES,
    default_apprise_config,
    default_notifications_config,
    merge_dict_defaults,
)


app = Flask(__name__, root_path=ROOT_DIR, static_folder="static", template_folder="static")
# secret_key is required for flash() to function
app.secret_key = token(24)
app.config.from_prefixed_env()
app.svc = ServiceManager()

sock = Sock(app)

PRINTERS_WITHOUT_CAMERA = ["V8110"]


def _deep_update(base, updates):
    if not isinstance(base, dict):
        base = {}
    if not isinstance(updates, dict):
        return base
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_update(base.get(key), value)
        else:
            base[key] = value
    return base


def _resolve_notifications(cfg):
    return merge_dict_defaults(getattr(cfg, "notifications", None), default_notifications_config())


def _resolve_apprise(cfg):
    notifications = _resolve_notifications(cfg)
    apprise = merge_dict_defaults(notifications.get("apprise"), default_apprise_config())
    progress = apprise.get("progress")
    if isinstance(progress, dict):
        progress.pop("max_value", None)
    return apprise


# autopep8: off
import web.service.pppp
import web.service.video
import web.service.mqtt
import web.service.filetransfer
# autopep8: on


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
    if not app.config["login"] or not app.config.get("video_supported"):
        return
    vq = app.svc.svcs.get("videoqueue")
    if not vq or not getattr(vq, "video_enabled", False):
        return
    for msg in app.svc.stream("videoqueue"):
        sock.send(msg.data)


@sock.route("/ws/pppp-state")
def pppp_state(sock):
    """
    Provides the status of the 'pppp' stream service through websocket
    """
    if not app.config["login"]:
        log.info("Websocket connection rejected: not logged in")
        return

    log.info("Starting PPPP state websocket handler")

    pppp = None
    pppp_connected = False
    last_keepalive = 0.0

    try:
        # Start PPPP service, but don't block the websocket waiting for it.
        pppp = app.svc.get("pppp", ready=False)

        while True:
            now = time.time()
            current_connected = bool(getattr(pppp, "connected", False))

            if current_connected and not pppp_connected:
                sock.send(json.dumps({"status": "connected"}))
                pppp_connected = True
                last_keepalive = now
            elif pppp_connected and not current_connected:
                sock.send(json.dumps({"status": "disconnected"}))
                break
            elif pppp_connected and now - last_keepalive >= 10.0:
                # Keepalive to detect client disconnects.
                sock.send(json.dumps({"status": "connected"}))
                last_keepalive = now

            time.sleep(1.0)
    except ConnectionClosed:
        log.info("WebSocket connection closed by client")
    except Exception as e:
        log.warning(f"Error in PPPP state websocket handler: {e}")
        log.info("Stack trace:", exc_info=True)
    finally:
        if pppp is not None:
            try:
                app.svc.put("pppp")
            except Exception:
                pass
        log.info("PPPP state websocket handler ending")


@sock.route("/ws/upload")
def upload(sock):
    """
    Provides upload progress updates through websocket
    """
    if not app.config["login"]:
        return
    for data in app.svc.stream("filetransfer"):
        sock.send(json.dumps(data))


@sock.route("/ws/ctrl")
def ctrl(sock):
    """
    Handles controlling of light and video quality through websocket
    """
    if not app.config["login"]:
        return

    # send a response on connect, to let the client know the connection is ready
    sock.send(json.dumps({"ankerctl": 1}))
    vq = app.svc.svcs.get("videoqueue")
    if vq:
        profile_id = getattr(vq, "saved_video_profile_id", None)
        if profile_id is None:
            profile_id = web.service.video.VIDEO_PROFILE_DEFAULT_ID
        sock.send(json.dumps({"video_profile": profile_id}))

    while True:
        msg = json.loads(sock.receive())

        if "light" in msg:
            with app.svc.borrow("videoqueue") as vq:
                vq.api_light_state(msg["light"])

        if "video_profile" in msg:
            with app.svc.borrow("videoqueue") as vq:
                vq.api_video_profile(msg["video_profile"])
        elif "quality" in msg:
            with app.svc.borrow("videoqueue") as vq:
                vq.api_video_mode(msg["quality"])
        if "video_enabled" in msg:
            vq = app.svc.svcs.get("videoqueue")
            if vq:
                vq.set_video_enabled(msg["video_enabled"])
                if msg["video_enabled"]:
                    if vq.state == RunState.Stopped:
                        vq.start()
                else:
                    if vq.state == RunState.Running:
                        vq.stop()


@app.get("/video")
def video_download():
    """
    Handles the video streaming/downloading feature in the Flask app
    """
    def generate():
        if not app.config["login"] or not app.config.get("video_supported"):
            return
        vq = app.svc.svcs.get("videoqueue")
        if vq:
            if not getattr(vq, "video_enabled", False):
                return
            if vq.state == RunState.Stopped:
                try:
                    vq.start()
                    vq.await_ready()
                except ServiceStoppedError:
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
            upload_rate_mbps = getattr(cfg, "upload_rate_mbps", None)
        else:
            anker_config = "No printers found, please load your login config..."
            printer = None
            upload_rate_mbps = None

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
            video_supported=app.config.get("video_supported", False),
            upload_rate_mbps=upload_rate_mbps,
            upload_rate_env=os.getenv("UPLOAD_RATE_MBPS"),
            upload_rate_choices=UPLOAD_RATE_MBPS_CHOICES,
            printer=printer,
            video_profiles=web.service.video.VIDEO_PROFILES,
            video_profile_default=web.service.video.VIDEO_PROFILE_DEFAULT_ID,
        )


@app.get("/api/version")
def app_api_version():
    """
    Returns the version details of api and server as dictionary

    Returns:
        A dictionary containing version details of api and server
    """
    return {"api": "0.1", "server": "1.9.0", "text": "OctoPrint 1.9.0"}


@app.post("/api/ankerctl/config/upload")
def app_api_ankerctl_config_upload():
    """
    Handles the uploading of configuration file to Flask server

    Returns:
        A HTML redirect response
    """
    if request.method != "POST":
        return web.util.flash_redirect(url_for('app_root'))
    if "login_file" not in request.files:
        return web.util.flash_redirect(url_for('app_root'), "No file found", "danger")
    file = request.files["login_file"]

    try:
        web.config.config_import(file, app.config["config"])
        return web.util.flash_redirect(url_for('app_api_ankerctl_server_reload'),
                                       "AnkerMake Config Imported!", "success")
    except web.config.ConfigImportError as err:
        log.exception(f"Config import failed: {err}")
        return web.util.flash_redirect(url_for('app_root'), f"Error: {err}", "danger")
    except Exception as err:
        log.exception(f"Config import failed: {err}")
        return web.util.flash_redirect(url_for('app_root'), f"Unexpected Error occurred: {err}", "danger")


@app.get("/api/ankerctl/server/reload")
def app_api_ankerctl_server_reload():
    """
    Reloads the Flask server

    Returns:
        A HTML redirect response
    """
    config = app.config["config"]

    with config.open() as cfg:
        app.config["login"] = bool(cfg)
        app.config["video_supported"] = any(
            printer.model not in PRINTERS_WITHOUT_CAMERA for printer in (cfg.printers if cfg else [])
        )
        if not cfg:
            return web.util.flash_redirect(url_for('app_root'), "No printers found in config", "warning")
        if "_flashes" in session:
            session["_flashes"].clear()
        if cfg and not app.svc.svcs:
            register_services(app)

        try:
            app.svc.restart_all(await_ready=False)
        except Exception as err:
            log.exception(err)
            return web.util.flash_redirect(url_for('app_root'), f"Ankerctl could not be reloaded: {err}", "danger")

        return web.util.flash_redirect(url_for('app_root'), "Ankerctl reloaded successfully", "success")


@app.post("/api/files/local")
def app_api_files_local():
    """
    Handles the uploading of files to Flask server

    Returns:
        A dictionary containing file details
    """
    user_name = request.headers.get("User-Agent", "ankerctl").split(url_for('app_root'))[0]

    no_act = not cli.util.parse_http_bool(request.form["print"])

    fd = request.files["file"]
    with app.config["config"].open() as cfg:
        rate_limit_mbps = cli.util.resolve_upload_rate_mbps(cfg)

    with app.svc.borrow("filetransfer") as ft:
        try:
            ft.send_file(fd, user_name, rate_limit_mbps=rate_limit_mbps, start_print=not no_act)
        except ConnectionError as E:
            log.error(f"Connection error: {E}")
            # This message will be shown in i.e. PrusaSlicer, so attempt to
            # provide a readable explanation.
            cli.util.http_abort(
                503,
                "Cannot connect to printer!\n" \
                "\n" \
                "Please verify that printer is online, and on the same network as ankerctl.\n" \
                "\n" \
                f"Exception information: {E}"
            )

    return {}


@app.post("/api/ankerctl/config/upload-rate")
def app_api_ankerctl_config_upload_rate():
    config = app.config["config"]
    if "upload_rate_mbps" not in request.form:
        return {"error": "upload_rate_mbps missing"}, 400

    try:
        rate_limit_mbps = int(request.form["upload_rate_mbps"])
    except ValueError:
        return {"error": "upload_rate_mbps must be an integer"}, 400

    if rate_limit_mbps not in UPLOAD_RATE_MBPS_CHOICES:
        return {"error": f"upload_rate_mbps must be one of {', '.join(map(str, UPLOAD_RATE_MBPS_CHOICES))}"}, 400

    with config.modify() as cfg:
        if not cfg:
            return {"error": "No printers configured"}, 400
        cfg.upload_rate_mbps = rate_limit_mbps

    return {"status": "ok", "upload_rate_mbps": rate_limit_mbps}


@app.get("/api/notifications/settings")
def app_api_notifications_settings():
    config = app.config["config"]
    with config.open() as cfg:
        if not cfg:
            return {"error": "No printers configured"}, 400
        apprise_config = _resolve_apprise(cfg)

    return {"apprise": apprise_config}


@app.post("/api/notifications/settings")
def app_api_notifications_settings_update():
    config = app.config["config"]
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {"error": "Invalid JSON payload"}, 400

    apprise_payload = payload.get("apprise") if "apprise" in payload else payload
    if not isinstance(apprise_payload, dict):
        return {"error": "Invalid apprise payload"}, 400

    with config.modify() as cfg:
        if not cfg:
            return {"error": "No printers configured"}, 400
        notifications = _resolve_notifications(cfg)
        apprise_config = _resolve_apprise(cfg)
        apprise_config = _deep_update(apprise_config, apprise_payload)
        notifications["apprise"] = apprise_config
        cfg.notifications = notifications

    return {"status": "ok", "apprise": apprise_config}


@app.post("/api/notifications/test")
def app_api_notifications_test():
    config = app.config["config"]
    payload = request.get_json(silent=True)
    apprise_payload = None
    if isinstance(payload, dict):
        apprise_payload = payload.get("apprise") if "apprise" in payload else payload
        if apprise_payload is not None and not isinstance(apprise_payload, dict):
            return {"error": "Invalid apprise payload"}, 400

    with config.open() as cfg:
        if not cfg:
            return {"error": "No printers configured"}, 400
        apprise_config = _resolve_apprise(cfg)

    if apprise_payload is not None:
        apprise_config = _deep_update(apprise_config, apprise_payload)

    # Use explicit settings for snapshot generation test
    from web.notifications import AppriseNotifier
    notifier = AppriseNotifier(config, settings=apprise_config)
    attachments, cleanup = notifier.build_attachments()

    client = AppriseClient(apprise_config)
    # Manually send via _post to bypass event checks for testing
    ok, message = client._post("Ankerctl Test", "Test notification sent from ankerctl settings page.", attachments=attachments)

    notifier.cleanup_attachments(cleanup)

    if ok:
        return {"status": "ok", "message": message}
    return {"error": message}, 400

@app.post("/api/printer/gcode")
def app_api_printer_gcode():
    payload = request.get_json(silent=True)
    if not payload or "gcode" not in payload:
        return {"error": "Missing gcode"}, 400

    gcode = payload["gcode"]
    with app.svc.borrow("mqttqueue") as mqtt:
        mqtt.send_gcode(gcode)

    return {"status": "ok"}


def register_services(app):
    app.svc.register("pppp", web.service.pppp.PPPPService())
    if app.config.get("video_supported"):
        app.svc.register("videoqueue", web.service.video.VideoQueue())
    app.svc.register("mqttqueue", web.service.mqtt.MqttQueue())
    app.svc.register("filetransfer", web.service.filetransfer.FileTransferService())


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
        if cfg and printer_index >= len(cfg.printers):
            log.critical(f"Printer number {printer_index} out of range, max printer number is {len(cfg.printers)-1} ")
        video_supported = False
        if cfg and printer_index < len(cfg.printers):
            video_supported = cfg.printers[printer_index].model not in PRINTERS_WITHOUT_CAMERA
        app.config["config"] = config
        app.config["login"] = bool(cfg)
        app.config["printer_index"] = printer_index
        app.config["port"] = port
        app.config["host"] = host
        app.config["insecure"] = insecure
        app.config["video_supported"] = video_supported
        app.config.update(kwargs)
        if cfg:
            register_services(app)
        app.run(host=host, port=port)
