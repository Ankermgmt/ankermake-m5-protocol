#!/usr/bin/env python3

import click
import logging
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
from libflagship.ppppapi import AnkerPPPPApi

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

@main.group("pppp", help="Low-level pppp api access")
def pppp(): pass

@main.group("http", help="Low-level http api access")
def http(): pass

@main.group("config", help="View and update configuration")
def config(): pass

@config.command("import")
@click.argument("filename", required=False)
@click.pass_obj
def config_import(obj, filename):
    """Import printer and account information from login.json"""
    print(f"config_import {filename}")

@config.command("show")
@click.pass_obj
def config_show(cfg):
    """Show current config"""

    with cfg.printers() as printers:
        if printers:
            print("Printers:")
            for p in printers:
                print(f"  {p}")
        else:
            log.error("No printers configured. Run 'config import' to populate.")

if __name__ == "__main__":
    main()
