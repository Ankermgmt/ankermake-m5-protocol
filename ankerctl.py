#!/usr/bin/env python3

import json
import click
import logging
import platform
from os import path
from rich import print

import cli.config
import cli.model
import cli.logfmt

import libflagship.httpapi
import libflagship.logincache
import libflagship.seccode

from libflagship.util import unhex, enhex
from libflagship.mqtt import MqttMsg, MqttMsgType
from libflagship.pppp import PktLanSearch
from libflagship.mqttapi import AnkerMQTTBaseClient
# from libflagship.ppppapi import AnkerPPPPApi

class AnkerMQTTClient(AnkerMQTTBaseClient):

    def on_connect(self, client, userdata, flags):
        log.info("Connected to mqtt")

    def on_message(self, client, userdata, msg, pkt, tail):
        log.info(f"TOPIC [{msg.topic}]")
        log.debug(enhex(msg.payload[:]))

        for obj in json.loads(pkt.data):
            try:
                cmdtype = obj["commandType"]
                name = MqttMsgType(cmdtype).name
                if name.startswith("ZZ_MQTT_CMD_"):
                    name = name[len("ZZ_MQTT_CMD_"):].lower()

                del obj["commandType"]
                print(f"  [{cmdtype:4}] {name:20} {obj}")
            except:
                print(f"  {obj}")

        if tail:
            log.warning(f"UNPARSED TAIL DATA: {tail}")

class Environment:
    def __init__(self):
        pass

pass_env = click.make_pass_decorator(Environment)

@click.group(context_settings = dict(help_option_names=["-h", "--help"], allow_interspersed_args=True))
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

    servertable = {
        "eu": "make-mqtt-eu.ankermake.com",
        "us": "make-mqtt.ankermake.com",
    }

    with env.config.open() as cfg:
        printer = cfg.printers[0]
        acct = cfg.account
        server = servertable[acct.region]
        log.info(f"Connecting to {server}")
        client = AnkerMQTTClient.login(
            printer.sn,
            acct.mqtt_username,
            acct.mqtt_password,
            printer.mqtt_key,
            ca_certs="examples/ankermake-mqtt.crt",
            verify=not env.insecure,
        )
        client.connect(server)
        client.loop()

@main.group("pppp", help="Low-level pppp api access")
def pppp(): pass

@main.group("http", help="Low-level http api access")
def http(): pass

@main.group("config", help="View and update configuration")
def config(): pass

@config.command("decode")
@click.argument("fd", required=True, type=click.File("r"), metavar="path/to/login.json")
@pass_env
def config_import(env, fd):
    """
    Decode a `login.json` file and print its contents.
    """

    log.info("Loading file..")

    cache = libflagship.logincache.load(fd.read())["data"]
    print(cache)

@config.command("import")
@click.argument("fd", required=False, type=click.File("r"), metavar="path/to/login.json")
@pass_env
def config_import(env, fd):
    """
    Import printer and account information from login.json

    When run without filename, attempt to auto-detect login.json in default
    install location
    """

    # if fd is not provided, try to auto-detect
    if fd is None:
        useros = platform.system()

        darfileloc = path.expanduser('~/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json')
        winfileloc = path.expandvars(r'%LOCALAPPDATA%\Ankermake\AnkerMake_64bit_fp\login.json')

        if useros == 'Darwin' and path.exists(darfileloc):
            fd = open(darfileloc, 'r')
        elif useros == 'Windows' and path.exists(winfileloc):
            fd = open(winfileloc, 'r')
        else:
            exit("This platform does not support autodetection. Please specify file location with -f <filename>")

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

    # save config
    env.config.save("default", config)

    log.info(f"Finished import")


@config.command("show")
@pass_env
def config_show(env):
    """Show current config"""

    with env.config.open() as cfg:
        if not cfg:
            log.error("No printers configured. Run 'config import' to populate.")
            return

        log.info("Account:")
        print(f"    user_id: {cfg.account.user_id[:20]}...")
        print(f"    email:   {cfg.account.email}")
        print(f"    region:  {cfg.account.region}")
        print()

        log.info("Printers:")
        for p in cfg.printers:
            print(f"    {p.sn}: {p.p2p_duid}")

if __name__ == "__main__":
    main()
