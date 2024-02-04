#!/usr/bin/env python3

import json
import click
import platform
import getpass
import webbrowser
import logging as log
from os import path, environ
from rich import print  # you need python3
from tqdm import tqdm

import cli.config
import cli.model
import cli.logfmt
import cli.mqtt
import cli.util
import cli.pppp
import cli.checkver  # check python version
import cli.countrycodes

import libflagship.httpapi
import libflagship.logincache
import libflagship.seccode

from libflagship.util import enhex
from libflagship.mqtt import MqttMsgType
from libflagship.pppp import PktLanSearch, P2PCmdType, P2PSubCmdType, FileTransfer
from libflagship.ppppapi import FileUploadInfo, PPPPError


class Environment:
    def __init__(self):
        pass

    def load_config(self, required=True):
        with self.config.open() as config:
            if not getattr(config, 'printers', False):
                msg = "No printers found in config. Please upload configuration " \
                    "using the webserver or 'ankerctl.py config import'"
                if required:
                    log.critical(msg)
                else:
                    log.warning(msg)

    def upgrade_config_if_needed(self):
        try:
            with self.config.open():
                pass
        except (KeyError, TypeError):
            log.warning("Outdated found. Attempting to refresh...")
            try:
                cli.config.attempt_config_upgrade(self.config, "default", self.insecure)
            except Exception as E:
                log.critical(f"Failed to refresh config. Please import configuration using 'config import' ({E})")


pass_env = click.make_pass_decorator(Environment)


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--pppp-dump", required=False, metavar="<file.log>", type=click.Path(),
              help="Enable logging of PPPP data to <file.log>")
@click.option("--insecure", "-k", is_flag=True, help="Disable TLS certificate validation")
@click.option("--verbose", "-v", count=True, help="Increase verbosity")
@click.option("--quiet", "-q", count=True, help="Decrease verbosity")
@click.option("--printer", "-p", type=int, default=environ.get('PRINTER_INDEX') or 0, help="Select printer number")
@click.pass_context
def main(ctx, pppp_dump, verbose, quiet, insecure, printer):
    ctx.ensure_object(Environment)
    env = ctx.obj
    levels = {
        -3: log.CRITICAL,
        -2: log.ERROR,
        -1: log.WARNING,
        0: log.INFO,
        1: log.DEBUG,
    }
    env.config   = cli.config.configmgr()
    env.insecure = insecure
    env.level = max(-3, min(verbose - quiet, 1))
    env.pppp_dump = pppp_dump

    cli.logfmt.setup_logging(levels[env.level])

    if insecure:
        import urllib3
        urllib3.disable_warnings()
        log.warning('[Not Verifying Certificates]')
        log.warning('This is insecure and should not be used in production environments.')
        log.warning('It is recommended to run without "-k/--insecure".')

    if ctx.invoked_subcommand not in {"http", "config"}:
        env.upgrade_config_if_needed()

    env.printer_index = printer
    log.debug(f"Using printer [{env.printer_index}]")


@main.group("mqtt", help="Low-level mqtt api access")
@pass_env
def mqtt(env):
    env.load_config()


@mqtt.command("monitor")
@pass_env
def mqtt_monitor(env):
    """
    Connect to mqtt broker, and show low-level events in realtime.
    """

    client = cli.mqtt.mqtt_open(env.config, env.printer_index, env.insecure)

    for msg, body in client.fetchloop():
        log.info(f"TOPIC [{msg.topic}]")
        log.debug(enhex(msg.payload[:]))

        for obj in body:
            try:
                cmdtype = obj["commandType"]
                name = MqttMsgType(cmdtype).name
                if name.startswith("ZZ_MQTT_CMD_"):
                    name = name[len("ZZ_MQTT_CMD_"):].lower()

                del obj["commandType"]
                print(f"  [{cmdtype:4}] {name:20} {obj}")
            except Exception:
                print(f"  {obj}")


@mqtt.command("send")
@click.argument("command-type", type=cli.util.EnumType(MqttMsgType), required=True, metavar="<cmd>")
@click.argument("args", type=cli.util.json_key_value, nargs=-1, metavar="[key=value] ...")
@click.option("--force", "-f", default=False, is_flag=True, help="Allow dangerous commands")
@pass_env
def mqtt_send(env, command_type, args, force):
    """
    Send raw command to printer via mqtt.

    BEWARE: This is intended for developers and experts only. Sending a
    malformed command can crash your printer, or have other unintended side
    effects.

    To see a list of known command types, run this command without arguments.
    """

    cmd = {
        "commandType": command_type,
        **{key: value for (key, value) in args},
    }

    if not force:
        if command_type == MqttMsgType.ZZ_MQTT_CMD_RECOVER_FACTORY.value:
            log.fatal("Refusing to perform factory reset (override with --force)")
            return

        if command_type == MqttMsgType.ZZ_MQTT_CMD_DEVICE_NAME_SET and "devName" not in cmd:
            log.fatal("Sending DEVICE_NAME_SET without devName=<name> will crash printer (override with --force)")
            return

    client = cli.mqtt.mqtt_open(env.config, env.printer_index, env.insecure)
    cli.mqtt.mqtt_command(client, cmd)


@mqtt.command("rename-printer")
@click.argument("newname", type=str, required=True, metavar="<newname>")
@pass_env
def mqtt_rename_printer(env, newname):
    """
    Set a new nickname for your printer
    """

    client = cli.mqtt.mqtt_open(env.config, env.printer_index, env.insecure)

    cmd = {
        "commandType": MqttMsgType.ZZ_MQTT_CMD_DEVICE_NAME_SET,
        "devName": newname
    }

    cli.mqtt.mqtt_command(client, cmd)


@mqtt.command("gcode")
@pass_env
def mqtt_gcode(env):
    """
    Interactive gcode command line. Send gcode command to the printer, and print the
    response.

    Press Ctrl-C to exit. (or Ctrl-D to close connection, except on Windows)
    """
    client = cli.mqtt.mqtt_open(env.config, env.printer_index, env.insecure)

    while True:
        gcode = click.prompt("gcode", prompt_suffix="> ")

        if not gcode:
            break

        cmd = {
            "commandType": MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND.value,
            "cmdData": gcode,
            "cmdLen": len(gcode),
        }

        client.command(cmd)
        msg = client.await_response(MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND)
        if msg:
            click.echo(msg["resData"])
        else:
            log.error("No response from printer")


@main.group("pppp", help="Low-level pppp api access")
def pppp(): pass


@pppp.command("lan-search")
@pass_env
def pppp_lan_search(env):
    """
    Attempt to find available printers on local LAN.

    Works by broadcasting a LAN_SEARCH packet, and waiting for a reply.
    """
    api = cli.pppp.pppp_open_broadcast(dumpfile=env.pppp_dump)
    try:
        api.send(PktLanSearch())
        resp = api.recv(timeout=1.0)
    except TimeoutError:
        log.error("No printers responded within timeout. Are you connected to the same network as the printer?")
    else:
        if isinstance(resp, libflagship.pppp.PktPunchPkt):
            log.info(f"Printer [{str(resp.duid)}] is online at {str(api.addr[0])}")


@pppp.command("print-file")
@click.argument("file", required=True, type=click.File("rb"), metavar="<file>")
@click.option("--no-act", "-n", is_flag=True, help="Test upload only (do not print)")
@pass_env
def pppp_print_file(env, file, no_act):
    """
    Transfer print job to printer, and start printing.

    The --no-act flag performs the upload, but will not make the printer start
    executing the print job. NOTE: the printer only ever stores ONE uploaded
    file, so anytime a file is uploaded, the old one is deleted.
    """
    env.load_config()
    api = cli.pppp.pppp_open(env.config, env.printer_index, dumpfile=env.pppp_dump)

    data = file.read()
    fui = FileUploadInfo.from_file(file.name, user_name="ankerctl", user_id="-", machine_id="-")
    log.info(f"Going to upload {fui.size} bytes as {fui.name!r}")
    try:
        cli.pppp.pppp_send_file(api, fui, data)
        if no_act:
            log.info("File upload complete")
        else:
            log.info("File upload complete. Requesting print start of job.")
            api.aabb_request(b"", frametype=FileTransfer.END)
    except PPPPError as E:
        log.error(f"Could not send print job: {E}")
    else:
        if not no_act:
            log.info("Successfully sent print job")
    finally:
        api.stop()


@pppp.command("capture-video")
@click.argument("file", required=True, type=click.File("wb"), metavar="<output.h264>")
@click.option("--max-size", "-m", required=True, type=cli.util.FileSizeType(),
              help="Stop capture at this size (kb, mb, gb, etc)")
@pass_env
def pppp_capture_video(env, file, max_size):
    """
    Capture video stream from printer camera.

    The output is in h264 ES (Elementary Stream) format. It can be played with
    "ffplay" from the ffmpeg program suite.
    """
    env.load_config()
    api = cli.pppp.pppp_open(env.config, env.printer_index, dumpfile=env.pppp_dump)

    cmd = {"commandType": P2PSubCmdType.START_LIVE, "data": {"encryptkey": "x", "accountId": "y"}}
    api.send_xzyh(json.dumps(cmd).encode(), cmd=P2PCmdType.P2P_JSON_CMD)
    try:
        with tqdm(unit="b", total=max_size, unit_scale=True, unit_divisor=1024) as bar:
            size = 0
            while True:
                d = api.recv_xzyh(chan=1)
                size += len(d.data)
                file.write(d.data)
                bar.set_postfix(size=cli.util.pretty_size(size), refresh=False)
                bar.update(len(d.data))
                if size >= max_size:
                    break
    finally:
        cmd = {"commandType": P2PSubCmdType.CLOSE_LIVE}
        api.send_xzyh(json.dumps(cmd).encode(), cmd=P2PCmdType.P2P_JSON_CMD)

    log.info(f"Successfully captured {cli.util.pretty_size(size)} video stream into {file.name}")


@main.group("http", help="Low-level http api access")
def http(): pass


@http.command("calc-check-code")
@click.argument("duid", required=True)
@click.argument("mac", required=True)
def http_calc_check_code(duid, mac):
    """
    Calculate printer 'check code' for http api version 1

    duid: Printer serial number (looks like EUPRAKM-012345-ABCDEF)

    mac: Printer mac address (looks like 11:22:33:44:55:66)
    """

    check_code = libflagship.seccode.calc_check_code(duid, mac.replace(":", ""))
    print(f"check_code: {check_code}")


@http.command("calc-sec-code")
@click.argument("duid", required=True)
@click.argument("mac", required=True)
def http_calc_sec_code(duid, mac):
    """
    Calculate printer 'security code' for http api version 2

    duid: Printer serial number (looks like EUPRAKM-012345-ABCDEF)

    mac: Printer mac address (looks like 11:22:33:44:55:66)
    """

    sec_ts, sec_code = libflagship.seccode.create_check_code_v1(duid.encode(), mac.replace(":", "").encode())
    print(f"sec_ts:   {sec_ts}")
    print(f"sec_code: {sec_code}")


@main.group("config", help="View and update configuration")
@click.pass_context
def config(ctx):
    if ctx.invoked_subcommand in {"import", "decode"}:
        return

    env = ctx.obj
    env.upgrade_config_if_needed()


@config.command("decode")
@click.argument("fd", required=False, type=click.File("r"), metavar="path/to/login.json")
@pass_env
def config_decode(env, fd):
    """
    Decode a `login.json` file and print its contents.
    """

    if fd is None:
        useros = platform.system()

        darfileloc = path.expanduser('~/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json')
        winfileloc1 = path.expandvars(r'%LOCALAPPDATA%\Ankermake\AnkerMake_64bit_fp\login.json')
        winfileloc2 = path.expandvars(r'%LOCALAPPDATA%\Ankermake\login.json')

        try:
            if useros == 'Darwin':
                fd = open(darfileloc, 'r')
            elif useros == 'Windows':
                if path.isfile(winfileloc1):
                    fd = open(winfileloc1, 'r')
                else:
                    fd = open(winfileloc2, 'r')
            else:
                log.critical("This platform does not support autodetection. Please specify file location")
        except FileNotFoundError:
            log.critical("Failed to import file - check if you are logged into Ankerslicer")

    log.info("Loading file..")

    cache = libflagship.logincache.load(fd.read())["data"]
    print(json.dumps(cache, indent=4))


@config.command("login")
@click.argument("country", required=False, metavar="[COUNTRY (2 letter code)]")
@click.argument("email", required=False)
@click.argument("password", required=False)
@pass_env
def config_login(env, country, email, password):
    """
    Fetch configuration by logging in with provided credentials.
    """

    try:
        with env.config.open() as cfg:
            if cfg.account:
                if country is None and cfg.account.country:
                    country = cfg.account.country
                    log.info(f"Country: {country.upper()}")
                if email is None:
                    email = cfg.account.email
                    log.info(f"Email address: {email}")
    except KeyError:
        pass

    # interactive user input (only if arguments not given on command line)
    if email is None:
        email = input("Please enter your email address: ").strip()

    if password is None:
        password = getpass.getpass("Please enter your password: ")

    if country:
        country = country.upper()
    while not cli.countrycodes.code_to_country(country):
        country = input("Please enter your country (2 digit code): ").strip().upper()

    region = libflagship.logincache.guess_region(country)
    login = None
    tries = 3
    captcha = {"id": None, "answer": None}
    # retry until login was successful
    while not login and tries > 0:
        tries -= 1
        try:
            login = cli.config.fetch_config_by_login(email, password, region, env.insecure,
                                                     captcha_id=captcha["id"], captcha_answer=captcha["answer"])
            break
        except libflagship.httpapi.APIError as E:
            # check if the error is actually a request to solve a captcha
            if E.json and "data" in E.json:
                data = E.json["data"]
                if "captcha_id" in data:
                    captcha = {
                        "id": data["captcha_id"],
                        "img": data["item"]
                    }

        # ask the user to resolve the captcha
        if captcha["id"]:
            log.warning(f"Login requires solving a captcha")
            if webbrowser.open(captcha["img"], new=2):
                captcha["answer"] = input("Please enter the captcha answer: ").strip()
            else:
                log.critical(f"Cannot open webbrowser for displaying captcha, aborting.")
                tries = 0
        else:
            log.critical(f"Unknown login error: {E}")
            tries = 0

    if login:
        log.info(f"Login successful, importing configuration from server..")

        # load remaining configuration items from the server
        cli.config.import_config_from_server(env.config, login, env.insecure)

        log.info("Finished import")


@config.command("import")
@click.argument("fd", required=False, type=click.File("r"), metavar="path/to/login.json")
@pass_env
def config_import(env, fd):
    """
    Import printer and account information from login.json

    When run without filename, attempt to auto-detect login.json in default
    install location
    """

    if fd is None:
        useros = platform.system()

        darfileloc = path.expanduser('~/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json')
        winfileloc1 = path.expandvars(r'%LOCALAPPDATA%\Ankermake\AnkerMake_64bit_fp\login.json')
        winfileloc2 = path.expandvars(r'%LOCALAPPDATA%\Ankermake\login.json')

        try:
            if useros == 'Darwin':
                fd = open(darfileloc, 'r')
            elif useros == 'Windows':
                if path.isfile(winfileloc1):
                    fd = open(winfileloc1, 'r')
                else:
                    fd = open(winfileloc2, 'r')
            else:
                log.critical("This platform does not support autodetection. Please specify file location")
        except FileNotFoundError:
            log.critical("Failed to import file - check if you are logged into Ankerslicer")

    log.info("Loading cache..")

    # load the login configuration from the provided file
    cache = libflagship.logincache.load(fd.read())["data"]

    # import the remaining configuration from the server
    cli.config.import_config_from_server(env.config, cache, env.insecure)

    log.info("Finished import")


@config.command("show")
@pass_env
def config_show(env):
    """Show current config"""

    log.info(f"Loading config from {env.config.config_path('default')}")
    print()

    # read config from json file named `ankerctl/default.json`
    with env.config.open() as cfg:
        if not cfg:
            log.error("No printers configured. Run 'config import' to populate.")
            return

        log.info("Account:")
        print(f"    user_id:    {cfg.account.user_id[:10]}...<REDACTED>")
        print(f"    auth_token: {cfg.account.auth_token[:10]}...<REDACTED>")
        print(f"    email:      {cfg.account.email}")
        print(f"    region:     {cfg.account.region.upper()}")
        print(f"    country:    {cfg.account.country.upper()}")
        print()

        log.info("Printers:")
        # Sort the list of printers by printer.id
        for i, p in enumerate(cfg.printers):
            print(f"    printer:   {i}")
            print(f"    id:        {p.id}")
            print(f"    name:      {p.name}")
            print(f"    duid:      {p.p2p_duid}") # Printer Serial Number
            print(f"    sn:        {p.sn}")
            print(f"    model:     {p.model}")
            print(f"    created:   {p.create_time}")
            print(f"    updated:   {p.update_time}")
            print(f"    ip:        {p.ip_addr}")
            print(f"    wifi_mac:  {cli.util.pretty_mac(p.wifi_mac)}")
            print(f"    api_hosts: {', '.join(p.api_hosts)}")
            print(f"    p2p_hosts: {', '.join(p.p2p_hosts)}")
            print()


@main.group("webserver", help="Built-in webserver support")
@pass_env
def webserver(env):
    env.load_config(False)


@webserver.command("run", help="Run ankerctl webserver")
@click.option("--host", default='127.0.0.1', envvar="FLASK_HOST", help="Network interface to bind to")
@click.option("--port", default=4470, envvar="FLASK_PORT", help="Port to bind to")
@pass_env
def webserver(env, host, port):
    import web
    web.webserver(env.config, env.printer_index, host, port, env.insecure, pppp_dump=env.pppp_dump)


if __name__ == "__main__":
    main()
