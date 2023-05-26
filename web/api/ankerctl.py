import json
import logging as log

from flask import Blueprint, session, request, url_for
from flask import current_app as app

import web.config
import web.util

router = Blueprint("ankerctl", __name__)


@router.post("/config/upload")
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
        return web.util.flash_redirect(url_for('ankerctl.app_api_ankerctl_server_reload'),
                                       "AnkerMake Config Imported!", "success")
    except web.config.ConfigImportError as err:
        log.exception(f"Config import failed: {err}")
        return web.util.flash_redirect(url_for('app_root'), f"Error: {err}", "danger")
    except Exception as err:
        log.exception(f"Config import failed: {err}")
        return web.util.flash_redirect(url_for('app_root'), f"Unexpected Error occurred: {err}", "danger")


@router.get("/server/reload")
def app_api_ankerctl_server_reload():
    """
    Reloads the Flask server

    Returns:
        A HTML redirect response
    """
    config = app.config["config"]

    with config.open() as cfg:
        app.config["login"] = bool(cfg)
        if not cfg:
            return web.util.flash_redirect(url_for('app_root'), "No printers found in config", "warning")
        if "_flashes" in session:
            session["_flashes"].clear()

        try:
            app.svc.restart_all(await_ready=False)
        except Exception as err:
            log.exception(err)
            return web.util.flash_redirect(url_for('app_root'), f"Ankerctl could not be reloaded: {err}", "danger")

        return web.util.flash_redirect(url_for('app_root'), "Ankerctl reloaded successfully", "success")


@router.post("/file/upload")
def app_api_ankerctl_file_upload():
    if request.method != "POST":
        return web.util.flash_redirect(url_for('app_root'))
    if "gcode_file" not in request.files:
        return web.util.flash_redirect(url_for('app_root'), "No file found", "danger")
    file = request.files["gcode_file"]

    try:
        web.util.upload_file_to_printer(app, file)
        return web.util.flash_redirect(url_for('app_root'),
                                       f"File {file.filename} sent to printer!", "success")
    except ConnectionError as err:
        return web.util.flash_redirect(url_for('app_root'),
                                       "Cannot connect to printer!\n"
                                       "Please verify that printer is online, and on the same network as ankerctl.\n"
                                       f"Exception information: {err}", "danger")
    except Exception as err:
        return web.util.flash_redirect(url_for('app_root'),
                                       f"Unknown error occurred: {err}", "danger")
