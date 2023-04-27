import os
import re
import json
import tempfile
import logging as log

from secrets import token_urlsafe as token

from flask import Flask, flash, request, redirect, url_for, render_template, Response, session
from flask_sock import Sock
from werkzeug.utils import secure_filename

import libflagship.httpapi
import libflagship.logincache

from libflagship.pppp import P2PSubCmdType, FileTransfer
from libflagship.ppppapi import FileUploadInfo, PPPPError


from web.lib.service import ServiceManager

from user_agents import parse

import cli.util
import cli.config


def dict_match(dict, match):
    for key in dict:
        if re.match(rf"^{key}.*", match):
            return key


app = Flask(
    __name__,
    root_path=".",
    static_folder="static",
    template_folder="static"
)
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
    if app.config["login"]:
        app.svc.register("pppp", web.service.pppp.PPPPService())
        app.svc.register("videoqueue", web.service.video.VideoQueue())
        app.svc.register("mqttqueue", web.service.mqtt.MqttQueue())
        app.svc.register("filetransfer", web.service.filetransfer.FileTransferService())


@sock.route("/ws/mqtt")
def mqtt(sock):

    if app.config["login"]:
        for data in app.svc.stream("mqttqueue"):
            log.debug(f"MQTT message: {data}")
            sock.send(json.dumps(data))


@sock.route("/ws/video")
def video(sock):

    if app.config["login"]:
        for msg in app.svc.stream("videoqueue"):
            sock.send(msg.data)


@sock.route("/ws/ctrl")
def ctrl(sock):

    if app.config["login"]:
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
        if app.config["login"]:
            for msg in app.svc.stream("videoqueue"):
                yield msg.data

    return Response(generate(), mimetype='video/mp4')


@app.get("/")
def app_root():
    config = app.config["config"]
    user_agent = parse(request.headers.get('User-Agent'))
    login_path = {
        'Mac OS': '~/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json',
        'Windows': r'%LOCALAPPDATA%\Ankermake\AnkerMake_64bit_fp\login.json',
        'None': 'Unsupported OS, supply path to login.json',
    }
    useros = dict_match(login_path, user_agent.os.family)

    host = request.host.split(':')
    requestPort = host[1] if len(host) > 1 else '80' # If there is no 2nd array entry, the request port is 80
    return render_template(
        "index.html",
        requestPort=requestPort,
        requestHost=host[0]
        configure=app.config["login"],
        loginFilePath=login_path[useros] if useros in login_path else login_path["None"],
        ankerConfig=str(config_show()) if app.config["login"] else '<p>No printers found, please load your login config...</p>',
    )


@app.get("/api/version")
def app_api_version():
    return {
        "api": "0.1",
        "server": "1.9.0",
        "text": "OctoPrint 1.9.0"
    }


def allowed_file(filename, ALLOWED_EXTENSIONS):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def config_show():
    config = app.config["config"]
    with config.open() as cfg:
        config_output = f'''<p>Account:</p><p>
            user_id:    {cfg.account.user_id[:10]}...[REDACTED] <br/>
            auth_token: {cfg.account.auth_token[:10]}...[REDACTED] <br/>
            email:      {cfg.account.email} <br/>
            region:     {cfg.account.region.upper()} </p
        '''
        config_output += '<p>Printers:</p><hr/>'
        for p in cfg.printers:
            config_output += f'''<p>
                duid:      {p.p2p_duid} <br/>
                sn:        {p.sn} <br/>
                ip:        {p.ip_addr} <br/>
                wifi_mac:  {cli.util.pretty_mac(p.wifi_mac)} <br/>
                api_hosts: {', '.join(p.api_hosts)} <br/>
                p2p_hosts: {', '.join(p.p2p_hosts)} <hr/></p>
            '''
        return config_output


def config_import(loginFile):
    file = open(loginFile, 'r')
    config = app.config["config"]

    # extract auth token
    cache = libflagship.logincache.load(file.read())["data"]
    auth_token = cache["auth_token"]

    # extract account region
    region = libflagship.logincache.guess_region(cache["ab_code"])

    try:
        newConfig = cli.config.load_config_from_api(auth_token, region, False)
    except libflagship.httpapi.APIError as E:
        flash(f"Config import failed: {E} (auth token might be expired: make sure Ankermake Slicer can connect, then try again", 'danger')
        return redirect('/')
    except Exception as E:
        flash(f"Config import failed: {E}", 'danger')
        return redirect('/')

    try:
        config.save("default", newConfig)
    except Exception as E:
        flash(f"Config import failed: {E}", 'danger')
        return redirect('/')
    flash("Configuration imported! Restarting...", 'success')
    return redirect('/')


@app.post('/api/config/upload')
def app_api_config_upload():
    ALLOWED_EXTENSIONS = set(['json'])
    with tempfile.TemporaryDirectory(prefix='ankerctl_') as tmpdir:
        config = app.config["config"]

        if request.method == 'POST':
            if 'loginFile' not in request.files:
                flash('No file found', 'danger')
                return redirect('/')
            file = request.files['loginFile']
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect('/')
            if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
                filename = secure_filename(file.filename)
                filepath = os.path.join(tmpdir, filename)
                file.save(filepath)
                config_import(filepath)
                return redirect('/reload')
            elif file and not allowed_file(file.filename, ALLOWED_EXTENSIONS):
                flash(f'File must be of type: {str(ALLOWED_EXTENSIONS)}', 'warning')
                return redirect('/')


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
        app.config["config"] = config
        app.config["login"] = True if cfg else False
        if cfg:
            session['_flashes'].clear()
            flash('Configuration loaded', 'success')
            startup()
            return redirect('/')


def webserver(config, host, port, **kwargs):
    with config.open() as cfg:
        app.config["config"] = config
        app.config["login"] = True if cfg else False
        app.config["port"] = port
        app.config["host"] = host
        app.config.update(kwargs)
        app.run(host=host, port=port)
