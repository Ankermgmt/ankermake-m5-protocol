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
    - /api/ankerctl/config/login: Performs email/password login and saves configuration
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
from flask import Flask, flash, request, render_template, Response, session, url_for, jsonify
from flask_sock import Sock
from simple_websocket.errors import ConnectionClosed
from user_agents import parse as user_agent_parse

from libflagship import ROOT_DIR
import libflagship.httpapi
import libflagship.logincache
from libflagship.notifications import AppriseClient

from web.lib.service import ServiceManager, RunState, ServiceStoppedError

import web.config
import web.platform
import web.util

import cli.util
import cli.config
import cli.countrycodes
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

# Configurable upload size limit (default: 2 GB)
max_upload_mb = int(os.getenv("UPLOAD_MAX_MB", "2048"))
app.config['MAX_CONTENT_LENGTH'] = max_upload_mb * 1024 * 1024

# Session cookie security
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_HTTPONLY'] = True

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
        log.info("Websocket connection rejected: no printer configured (use 'config import' or 'config login')")
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
            if isinstance(msg["light"], bool):
                with app.svc.borrow("videoqueue") as vq:
                    vq.api_light_state(msg["light"])
            else:
                log.warning(f"Invalid 'light' value (expected bool): {msg['light']!r}")

        if "video_profile" in msg:
            if isinstance(msg["video_profile"], int):
                with app.svc.borrow("videoqueue") as vq:
                    vq.api_video_profile(msg["video_profile"])
            else:
                log.warning(f"Invalid 'video_profile' value (expected int): {msg['video_profile']!r}")
        elif "quality" in msg:
            if isinstance(msg["quality"], int):
                with app.svc.borrow("videoqueue") as vq:
                    vq.api_video_mode(msg["quality"])
            else:
                log.warning(f"Invalid 'quality' value (expected int): {msg['quality']!r}")

        if "video_enabled" in msg:
            if not isinstance(msg["video_enabled"], bool):
                log.warning(f"Invalid 'video_enabled' value (expected bool): {msg['video_enabled']!r}")
                continue
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
            config_existing_email = cfg.account.email
            printer = cfg.printers[app.config["printer_index"]]
            upload_rate_mbps = getattr(cfg, "upload_rate_mbps", None)
            country = cfg.account.country
        else:
            anker_config = "No printers found, please load your login config..."
            config_existing_email = ""
            printer = None
            upload_rate_mbps = None
            country = ""

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
            config_existing_email=config_existing_email,
            country_codes=json.dumps(cli.countrycodes.country_codes),
            current_country=country,
            video_supported=app.config.get("video_supported", False),
            upload_rate_mbps=upload_rate_mbps,
            upload_rate_env=os.getenv("UPLOAD_RATE_MBPS"),
            upload_rate_choices=UPLOAD_RATE_MBPS_CHOICES,
            printer=printer,
            video_profiles=web.service.video.VIDEO_PROFILES,
            video_profile_default=web.service.video.VIDEO_PROFILE_DEFAULT_ID,
            print_controls_enabled=bool(os.getenv("ANKERCTL_PRINT_CONTROLS")),
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
        session["authenticated"] = True
        return web.util.flash_redirect(url_for('app_api_ankerctl_server_reload'),
                                       "AnkerMake Config Imported!", "success")
    except web.config.ConfigImportError as err:
        log.exception(f"Config import failed: {err}")
        return web.util.flash_redirect(url_for('app_root'), "Config import failed. Check server logs for details.", "danger")
    except Exception as err:
        log.exception(f"Config import failed: {err}")
        return web.util.flash_redirect(url_for('app_root'), "An unexpected error occurred. Check server logs for details.", "danger")


@app.post("/api/ankerctl/config/login")
def app_api_ankerctl_config_login():
    if request.method != "POST":
        flash(f"Invalid request method '{request.method}", "danger")
        return jsonify({"redirect": url_for('app_root')})

    form_data = request.form.to_dict()

    for key in ["login_email", "login_password", "login_country"]:
        if key not in form_data:
            return jsonify({"error": f"Error: Missing form entry '{key}'"})

    if not cli.countrycodes.code_to_country(form_data["login_country"]):
        return jsonify({"error": f"Error: Invalid country code '{form_data['login_country']}'"})

    try:
        web.config.config_login(
            form_data['login_email'],
            form_data['login_password'],
            form_data['login_country'],
            form_data.get('login_captcha_id', ''),
            form_data.get('login_captcha_text', ''),
            app.config["config"],
        )
        flash("AnkerMake Config Imported!", "success")
        session["authenticated"] = True
        return jsonify({"redirect": url_for('app_api_ankerctl_server_reload')})
    except web.config.ConfigImportError as err:
        if err.captcha:
            return jsonify({"captcha_id": err.captcha["id"], "captcha_url": err.captcha["img"]})
        log.exception(f"Config login failed: {err}")
        flash("Login failed. Check server logs for details.", "danger")
        return jsonify({"redirect": url_for('app_root')})
    except Exception as err:
        log.exception(f"Config login failed: {err}")
        flash("An unexpected error occurred. Check server logs for details.", "danger")
        return jsonify({"redirect": url_for('app_root')})


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
                "Please verify that printer is online, and on the same network as ankerctl."
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

# GCode prefixes that are unsafe to send while a print is active
_UNSAFE_GCODE_PREFIXES = {"G0", "G1", "G28", "G29", "G91", "G90"}

@app.post("/api/printer/gcode")
def app_api_printer_gcode():
    payload = request.get_json(silent=True)
    if not payload or "gcode" not in payload:
        return {"error": "Missing gcode"}, 400

    gcode = payload["gcode"]
    lines = [line.strip() for line in gcode.split('\n') if line.strip()]

    with app.svc.borrow("mqttqueue") as mqtt:
        if mqtt.is_printing:
            unsafe = [l for l in lines if l.split()[0].upper() in _UNSAFE_GCODE_PREFIXES]
            if unsafe:
                return {"error": "Motion commands blocked while printing"}, 409
        mqtt.send_gcode(gcode)

    return {"status": "ok"}


@app.post("/api/printer/control")
def app_api_printer_control():
    payload = request.get_json(silent=True)
    if not payload or "value" not in payload:
        return {"error": "Missing value"}, 400

    try:
        value = int(payload["value"])
    except (ValueError, TypeError):
        return {"error": "Value must be an integer"}, 400

    with app.svc.borrow("mqttqueue") as mqtt:
        mqtt.send_print_control(value)

    return {"status": "ok"}


@app.post("/api/printer/autolevel")
def app_api_printer_autolevel():
    with app.svc.borrow("mqttqueue") as mqtt:
        if mqtt.is_printing:
            return {"error": "Auto-leveling blocked while printing"}, 409
        mqtt.send_auto_leveling()
    return {"status": "ok"}


@app.get("/api/snapshot")
def app_api_snapshot():
    """Capture a JPEG snapshot from the camera and return it as a file download."""
    import shutil
    import subprocess
    import tempfile

    if not app.config.get("video_supported"):
        return {"error": "Video not supported on this platform"}, 400

    if not shutil.which("ffmpeg"):
        return {"error": "ffmpeg not installed"}, 500

    vq = app.svc.svcs.get("videoqueue")
    if not vq:
        return {"error": "Video service not available"}, 503

    host = os.getenv("FLASK_HOST") or "127.0.0.1"
    if host in {"0.0.0.0", "::"}:
        host = "127.0.0.1"
    port = os.getenv("FLASK_PORT") or "4470"
    url = f"http://{host}:{port}/video"

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_path = temp_file.name
    temp_file.close()

    try:
        result = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-nostdin", "-y",
             "-f", "h264", "-i", url, "-frames:v", "1", temp_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
        )
        if result.returncode != 0:
            # Retry without -f h264
            result = subprocess.run(
                ["ffmpeg", "-loglevel", "error", "-nostdin", "-y",
                 "-i", url, "-frames:v", "1", temp_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
            )
        if result.returncode != 0 or not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            return {"error": "Snapshot capture failed"}, 500

        from flask import send_file
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return send_file(temp_path, mimetype="image/jpeg",
                         as_attachment=True,
                         download_name=f"ankerctl_snapshot_{timestamp}.jpg")
    except (subprocess.TimeoutExpired, OSError) as err:
        return {"error": f"Snapshot failed: {err}"}, 500
    finally:
        # Clean up after send_file has read the data
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass

@app.get("/api/history")
def app_api_history():
    """Return print history as JSON with pagination."""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    with app.svc.borrow("mqttqueue") as mqtt:
        entries = mqtt.history.get_history(limit=limit, offset=offset)
        total = mqtt.history.get_count()
    return {"entries": entries, "total": total}


@app.delete("/api/history")
def app_api_history_clear():
    """Clear all print history."""
    with app.svc.borrow("mqttqueue") as mqtt:
        mqtt.history.clear()
    return {"status": "ok"}


@app.get("/api/timelapses")
def app_api_timelapses():
    """List available timelapse videos."""
    with app.svc.borrow("mqttqueue") as mqtt:
        videos = mqtt.timelapse.list_videos()
    return {"videos": videos, "enabled": mqtt.timelapse.enabled}


@app.get("/api/timelapse/<filename>")
def app_api_timelapse_download(filename):
    """Download a timelapse video."""
    from flask import send_file
    with app.svc.borrow("mqttqueue") as mqtt:
        path = mqtt.timelapse.get_video_path(filename)
    if not path:
        return {"error": "Video not found"}, 404
    return send_file(path, mimetype="video/mp4", as_attachment=True, download_name=filename)


@app.delete("/api/timelapse/<filename>")
def app_api_timelapse_delete(filename):
    """Delete a timelapse video."""
    with app.svc.borrow("mqttqueue") as mqtt:
        deleted = mqtt.timelapse.delete_video(filename)
    if not deleted:
        return {"error": "Video not found"}, 404
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
    # Resolve API key: ENV var takes precedence over config file
    api_key = cli.config.resolve_api_key(config)
    app.config["api_key"] = api_key
    if api_key:
        log.info(f"API key authentication enabled (key: {api_key[:4]}...{api_key[-4:]})")
    else:
        log.info("No API key set. Authentication disabled.")

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

# GET endpoints that modify state and require auth despite being GET
_PROTECTED_GET_PATHS = {
    "/api/ankerctl/server/reload",
}

# POST endpoints needed for initial printer setup (config import / login)
_SETUP_PATHS = {
    "/api/ankerctl/config/upload",
    "/api/ankerctl/config/login",
}


@app.before_request
def _check_api_key():
    """Middleware: enforce API key on write operations (POST/PUT/DELETE).

    Read-only requests (GET) are allowed without auth so the WebUI
    stays accessible.  The API key is only required for mutations.
    Setup endpoints are exempted when no printer is configured yet.
    """
    api_key = app.config.get("api_key")
    if not api_key:
        # No key configured → allow all requests (backwards compatible)
        return None

    # Allow static assets without auth
    if request.path.startswith("/static/"):
        return None

    # Allow read-only (GET/HEAD/OPTIONS) unless the path is explicitly protected
    if request.method in ("GET", "HEAD", "OPTIONS") and request.path not in _PROTECTED_GET_PATHS:
        return None

    # Allow setup endpoints when no printer is configured yet
    if not app.config.get("login") and request.path in _SETUP_PATHS:
        return None

    # --- From here on, auth is required ---

    # Check X-Api-Key header (slicer / programmatic access)
    if request.headers.get("X-Api-Key") == api_key:
        return None

    # Check ?apikey= URL parameter → set session cookie and redirect
    url_key = request.args.get("apikey")
    if url_key == api_key:
        session["authenticated"] = True
        # Remove apikey from URL to avoid it staying in browser history
        from urllib.parse import urlencode, urlparse, parse_qs
        parsed = urlparse(request.url)
        params = parse_qs(parsed.query)
        params.pop("apikey", None)
        clean_url = request.path
        if params:
            clean_url += "?" + urlencode(params, doseq=True)
        from flask import redirect
        return redirect(clean_url)

    # Check session cookie (browser)
    if session.get("authenticated"):
        return None

    # Unauthorized
    return jsonify({"error": "Unauthorized. Provide API key via X-Api-Key header or ?apikey= parameter."}), 401
