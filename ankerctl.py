#!/usr/bin/env python3

import json
import click
import socket
import logging
import platform
from os import path
from rich import print

import cli.config
import cli.model
import cli.logfmt
import cli.mqtt
import cli.util

import libflagship.httpapi
import libflagship.logincache
import libflagship.seccode

from libflagship.util import unhex, enhex
from libflagship.mqtt import MqttMsgType
from libflagship.pppp import PktLanSearch
from libflagship.ppppapi import AnkerPPPPApi

class Environment:
    def __init__(self):
        pass

pass_env = click.make_pass_decorator(Environment)

@click.group(context_settings = dict(help_option_names=["-h", "--help"]))
@click.option("--insecure", "-k", is_flag=True, help="Disable TLS certificate validation")
@click.option("--verbose", "-v", count=True, help="Increase verbosity")
@click.option("--quiet", "-q", count=True, help="Decrease verbosity")
@click.pass_context
def main(ctx, verbose, quiet, insecure):
    ctx.ensure_object(Environment)
    env = ctx.obj

    levels = {
        -3: logging.CRITICAL,
        -2: logging.ERROR,
        -1: logging.WARNING,
        0: logging.INFO,
        1: logging.DEBUG,
    }
    env.config   = cli.config.configmgr()
    env.insecure = insecure
    env.level = max(-3, min(verbose - quiet, 1))
    env.log = cli.logfmt.setup_logging(levels[env.level])

    global log
    log = env.log

    if insecure:
        import urllib3
        urllib3.disable_warnings()

@main.group("mqtt", help="Low-level mqtt api access")
def mqtt(): pass

@mqtt.command("monitor")
@pass_env
def mqtt_monitor(env):
    """
    Connect to mqtt broker, and show low-level events in realtime.
    """

    client = cli.mqtt.mqtt_open(env)

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
            except:
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
    if not force:
        if command_type == MqttMsgType.ZZ_MQTT_CMD_APP_RECOVER_FACTORY.value:
            log.fatal("Refusing to perform factory reset (enable with --force)")

    cmd = {
        "commandType": command_type,
        **{key: value for (key, value) in args},
    }
    client = cli.mqtt.mqtt_open(env)
    client.command(cmd)

    msg = client.await_response(command_type)
    if msg:
        click.echo(cli.util.pretty_json(msg))
    else:
        log.error("No response from printer")

@mqtt.command("gcode")
@pass_env
def mqtt_gcode(env):
    """
    Interactive gcode command line. Send gcode command to the printer, and print the
    response.

    Press Ctrl-C to exit. (or Ctrl-D to close connection, except on Windows)
    """
    client = cli.mqtt.mqtt_open(env)

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
    api = AnkerPPPPApi.open_broadcast(timeout=1.0)
    try:
        resp = api.req(PktLanSearch())
    except TimeoutError:
        log.error("No printers responded within timeout. Are you connected to the same network as the printer?")
    else:
        if isinstance(resp, libflagship.pppp.PktPunchPkt):
            log.info(f"Printer [{str(resp.duid)}] is online")

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
def config(): pass

@config.command("decode")
@click.argument("fd", required=False, type=click.File("r"), metavar="path/to/login.json")
@pass_env
def config_import(env, fd):
    """
    Decode a `login.json` file and print its contents.
    """

    if fd is None:
        useros = platform.system()

        darfileloc = path.expanduser('~/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json')
        winfileloc = path.expandvars(r'%LOCALAPPDATA%\Ankermake\AnkerMake_64bit_fp\login.json')

        if useros == 'Darwin' and path.exists(darfileloc):
            fd = open(darfileloc, 'r')
        elif useros == 'Windows' and path.exists(winfileloc):
            fd = open(winfileloc, 'r')
        else:
            exit("This platform does not support autodetection. Please specify file location")

    log.info("Loading file..")

    cache = libflagship.logincache.load(fd.read())["data"]
    print(json.dumps(cache, indent=4))

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
        winfileloc = path.expandvars(r'%LOCALAPPDATA%\Ankermake\AnkerMake_64bit_fp\login.json')

        if useros == 'Darwin' and path.exists(darfileloc):
            fd = open(darfileloc, 'r')
        elif useros == 'Windows' and path.exists(winfileloc):
            fd = open(winfileloc, 'r')
        else:
            exit("This platform does not support autodetection. Please specify file location")

    log.info("Loading cache..")

    # extract auth token
    cache = libflagship.logincache.load(fd.read())["data"]
    auth_token=cache["auth_token"]

    # extract account region
    region=libflagship.logincache.guess_region(cache["ab_code"])

    log.info("Initializing API..")
    appapi = libflagship.httpapi.AnkerHTTPAppApiV1(auth_token=auth_token, region=region, verify=not env.insecure)
    ppapi = libflagship.httpapi.AnkerHTTPPassportApiV1(auth_token=auth_token, region=region, verify=not env.insecure)

    # request profile and printer list
    log.info("Requesting profile data..")
    profile = ppapi.profile()

    # create config object
    config = cli.model.Config(account=cli.model.Account(
        auth_token=auth_token,
        region=region,
        user_id=profile['user_id'],
        email=profile["email"],
    ), printers=[])

    log.info("Requesting printer list..")
    printers = appapi.query_fdm_list()

    log.info("Requesting pppp keys..")
    sns = [pr["station_sn"] for pr in printers]
    dsks = {dsk["station_sn"]: dsk for dsk in appapi.equipment_get_dsk_keys(station_sns=sns)["dsk_keys"]}

    # populate config object with printer list
    for pr in printers:
        station_sn = pr["station_sn"]
        config.printers.append(cli.model.Printer(
            sn=station_sn,
            mqtt_key=unhex(pr["secret_key"]),
            p2p_conn=pr["p2p_conn"],
            p2p_duid=pr["p2p_did"],
            p2p_key=dsks[pr["station_sn"]]["dsk_key"],
        ))
        log.info(f"Adding printer [{station_sn}]")

    # save config to json file named `ankerctl/default.json`
    env.config.save("default", config)

    log.info(f"Finished import")


@config.command("show")
@pass_env
def config_show(env):
    """Show current config"""

    # read config from json file named `ankerctl/default.json`
    with env.config.open() as cfg:
        if not cfg:
            log.error("No printers configured. Run 'config import' to populate.")
            return

        log.info("Account:")
        print(f"    user_id: {cfg.account.user_id[:20]}...<REDACTED>")
        print(f"    email:   {cfg.account.email}")
        print(f"    region:  {cfg.account.region}")
        print()

        log.info("Printers:")
        for p in cfg.printers:
            print(f"    sn: {p.sn}")
            print(f"    duid: {p.p2p_duid}") # Printer Serial Number

if __name__ == "__main__":
    main()
